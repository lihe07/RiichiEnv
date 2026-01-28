
import torch
import numpy as np
from torchrl.data import TensorDictReplayBuffer, LazyMemmapStorage, TensorDictPrioritizedReplayBuffer
from torchrl.data.replay_buffers.samplers import SamplerWithoutReplacement, PrioritizedSampler
from tensordict import TensorDict

class GlobalReplayBuffer:
    def __init__(self, 
                 actor_capacity: int = 10000, 
                 critic_capacity: int = 100000,
                 batch_size: int = 32,
                 device: str = "cpu"):
        
        self.device = torch.device(device)
        self.batch_size = batch_size
        
        # 1. Actor Buffer (FIFO / Sliding Window)
        # Keeps only recent data for PPO
        self.actor_buffer = TensorDictReplayBuffer(
            storage=LazyMemmapStorage(actor_capacity),
            sampler=SamplerWithoutReplacement(),
            batch_size=batch_size,
        )
        
        # 2. Critic Buffer (Prioritized)
        # Keeps long history for CQL
        try:
            self.critic_buffer = TensorDictPrioritizedReplayBuffer(
                storage=LazyMemmapStorage(critic_capacity),
                alpha=0.6,
                beta=0.4,
                batch_size=batch_size,
            )
        except RuntimeError:
            print("Warning: PrioritizedReplayBuffer not available (C++ extension missing). Using standard ReplayBuffer.")
            self.critic_buffer = TensorDictReplayBuffer(
                storage=LazyMemmapStorage(critic_capacity),
                sampler=SamplerWithoutReplacement(),
                batch_size=batch_size,
            )

    def add(self, transitions: list[dict]):
        """
        Adds a list of transitions to both buffers.
        Transitions should be a list of dicts with keys: 
        'features', 'mask', 'action', 'reward', 'done', 'policy_version', 'q_val'
        """
        if not transitions:
            return

        # Convert list of dicts to TensorDict
        # We assume all items are Tensors or compatible
        # Stack them
        
        # Optimization: Pre-allocate or use TensorDict.from_dict if possible
        # But for diverse list, looping is safer first.
        
        # Structure check
        # features: (46, 34)
        # mask: (82,)
        
        data_list = []
        for t in transitions:
            # Handle Numpy/Scalar inputs from Ray Worker
            # features: (46, 34) numpy
            # mask: (82,) numpy
            
            td = TensorDict({
                "features": torch.from_numpy(t["features"]), 
                "mask": torch.from_numpy(t["mask"]),         
                "action": torch.tensor(t["action"]),         
                "reward": torch.tensor(t["reward"]),         
                "done": torch.tensor(t["done"], dtype=torch.bool), # Preserve bool for now, cast later if needed? -> Reward usually float, Done bool/int
                "policy_version": torch.tensor(t["policy_version"]),
                "log_prob": torch.tensor(t["log_prob"]),     
            }, batch_size=[])
            data_list.append(td)
            
        batch = torch.stack(data_list)
        
        # Add to Actor Buffer (Old data falls off)
        self.actor_buffer.extend(batch)
        
        # Add to Critic Buffer (Prioritized)
        # Initial priority is default (max)
        self.critic_buffer.extend(batch)

    
    def update_beta(self, beta: float):
        """Update beta for Importance Sampling"""
        if hasattr(self.critic_buffer, "_sampler") and hasattr(self.critic_buffer._sampler, "_beta"):
             self.critic_buffer._sampler._beta = beta

    def sample_actor(self, batch_size=None):
        """Sample from recent data (PPO)"""
        if batch_size is None:
            batch_size = self.batch_size
        return self.actor_buffer.sample(batch_size=batch_size).to(self.device)

    def sample_critic(self, batch_size=None):
        """
        Sample from historical data (CQL) with Importance Sampling.
        Returns TensorDict with 'index' and '_weight' keys if using prioritized buffer.
        """
        if batch_size is None:
            batch_size = self.batch_size
            
        # TorchRL's Prioritized Replay Buffer automatically adds 'index' and '_weight' 
        # to the sampled TensorDict if configured correctly.
        batch = self.critic_buffer.sample(batch_size=batch_size).to(self.device)
        
        # Ensure _weight is 1.0 if not present (fallback)
        if "_weight" not in batch.keys():
            batch["_weight"] = torch.ones(batch_size, device=self.device)
            
        if "index" not in batch.keys():
             # Create dummy indices if not present (should not happen with prioritized buffer, but safe fallback)
             # Warning: Updating priority won't work without valid indices.
             batch["index"] = torch.zeros(batch_size, dtype=torch.long, device=self.device)

        return batch

    def update_priority(self, index, priority):
        """Update priorities for Critic Buffer"""
        if hasattr(self.critic_buffer, "update_priority"):
            self.critic_buffer.update_priority(index, priority)
