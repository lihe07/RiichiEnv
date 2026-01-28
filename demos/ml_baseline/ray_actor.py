
import ray
import torch
import numpy as np
from torch.distributions import Categorical
from riichienv import RiichiEnv
from unified_model import UnifiedNetwork

@ray.remote
class MahjongWorker:
    def __init__(self, worker_id: int, device: str = "cpu"):
        torch.set_num_threads(1)
        self.worker_id = worker_id
        self.device = torch.device(device)
        self.env = RiichiEnv(game_mode="4p-red-half")
        
        # Policy Model (Unified)
        self.model = UnifiedNetwork(in_channels=46, num_actions=82).to(self.device)
        self.model.eval()
        
        self.policy_version = 0

    def update_weights(self, state_dict, policy_version):
        """Syncs weights from the Learner."""
        self.model.load_state_dict(state_dict)
        self.policy_version = policy_version

    def _encode_obs(self, obs):
        """Encodes Rust observation to Torch Tensor."""
        feat = np.frombuffer(obs.encode(), dtype=np.float32).reshape(46, 34).copy()
        mask = np.frombuffer(obs.mask(), dtype=np.uint8).copy()
        # feat: (46, 34)
        return (
            torch.from_numpy(feat).to(self.device),
            torch.from_numpy(mask).to(self.device)
        )

    def collect_episode(self):
        """
        Runs one full episode of self-play.
        Returns a list of transitions for the learner.
        """
        self.env = RiichiEnv(game_mode="4p-red-half")
        obs_dict = self.env.reset()
        
        # key: player_id, value: list of steps
        episode_buffer = {0: [], 1: [], 2: [], 3: []}
        
        while not self.env.done():
            steps = {}
            for pid, obs in obs_dict.items():
                # 1. Observation
                feat_tensor, mask_tensor = self._encode_obs(obs)
                
                # 2. Policy Step (Stochastic Sampling for PPO)
                with torch.no_grad():
                    # Forward returns (logits, q_values)
                    logits, _ = self.model(feat_tensor.unsqueeze(0)) # (1, 82)
                    
                    # Apply Mask
                    # Set illegal actions to very small number
                    logits = logits.masked_fill(mask_tensor.unsqueeze(0) == 0, -1e9)
                    
                    # Create distribution
                    dist = Categorical(logits=logits)
                    action = dist.sample()
                    log_prob = dist.log_prob(action)
                    
                    
                    action_idx = action.item()
                    
                # 3. Step Environment
                found_action = obs.find_action(action_idx)
                if found_action is None:
                    legal_actions = obs.legal_actions()
                    if len(legal_actions) == 0:
                         # Log fatal state and break to avoid infinite loop
                         print(f"FATAL: Empty Legal Actions for PID {obs.player_id}")
                         print(f"Hand: {obs.hand}")
                         print(f"Melds: {obs.melds[obs.player_id]}")
                         break
                         
                    found_action = legal_actions[0]

                steps[pid] = found_action
                
                # 4. Store step (for PPO)
                episode_buffer[pid].append({
                    "features": feat_tensor.cpu().numpy(),
                    "mask": mask_tensor.cpu().numpy(),
                    "action": action_idx, # Scalar
                    "log_prob": log_prob.cpu().item(), # Scalar
                    "policy_version": self.policy_version, 
                })

            obs_dict = self.env.step(steps)
            
        # End of Episode
        final_scores = self.env.scores()
        ranks = self.env.ranks()
        transitions = []
        
        # Calculate Rewards
        for pid in range(4):
            rank = ranks[pid]
            
            # Scaled Rank Reward [10.0, 4.0, -4.0, -10.0]
            # RiichiEnv returns 1-based ranks (1, 2, 3, 4)
            obs_reward = 0.0
            if rank == 1: obs_reward = 10.0
            elif rank == 2: obs_reward = 4.0
            elif rank == 3: obs_reward = -4.0
            elif rank == 4: obs_reward = -10.0
            
            traj = episode_buffer[pid]
            T = len(traj)
            
            for t, step in enumerate(traj):
                # MC Return G_t
                gamma = 0.99
                decayed_return = obs_reward * (gamma ** (T - t - 1))
                
                # We store 'reward' = G_t because PPO Learner will sample this 
                # and use it as target.
                step["reward"] = np.array(decayed_return, dtype=np.float32)
                step["done"] = bool(t == T-1)
                
                transitions.append(step)
                
        return transitions
