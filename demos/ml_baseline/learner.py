import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical

from unified_model import UnifiedNetwork


class MahjongLearner:
    def __init__(self,
                 device: str = "cuda",
                 actor_lr: float = 1e-4,
                 critic_lr: float = 3e-4,
                 alpha_cql_init: float = 1.0,
                 alpha_cql_final: float = 0.1,
                 gamma: float = 0.99,
                 awac_beta: float = 0.3,
                 awac_max_weight: float = 20.0):

        self.device = torch.device(device)
        self.alpha_cql_init = alpha_cql_init
        self.alpha_cql_final = alpha_cql_final
        self.gamma = gamma
        self.awac_beta = awac_beta
        self.awac_max_weight = awac_max_weight

        self.model = UnifiedNetwork(num_actions=82).to(self.device)

        shared_lr = (actor_lr + critic_lr) / 2.0

        self.optimizer = optim.Adam([
            {'params': self.model.actor_head.parameters(), 'lr': actor_lr},
            {'params': self.model.critic_head.parameters(), 'lr': critic_lr},
            {'params': self.model.conv_in.parameters(), 'lr': shared_lr},
            {'params': self.model.bn_in.parameters(), 'lr': shared_lr},
            {'params': [p for block in self.model.res_blocks for p in block.parameters()], 'lr': shared_lr},
            {'params': self.model.fc_shared.parameters(), 'lr': shared_lr},
        ])

        self.mse_loss = nn.MSELoss(reduction='none')
        self.total_steps = 0

    def get_weights(self):
        return self.model.state_dict()

    def load_cql_weights(self, path: str):
        """
        Load weights from either:
        1. UnifiedNetwork checkpoint (has actor_head/critic_head) - for fine-tuning
        2. Offline CQL model (QNetwork with fc1/fc2) - for initial training

        UnifiedNetwork architecture: CNN -> fc_shared(2176->256) -> actor_head/critic_head(256->82)
        Old QNetwork architecture: CNN -> fc1(2176->256) -> fc2(256->82)

        If loading from QNetwork, mapping is:
        - CNN backbone: direct copy
        - fc1 -> fc_shared
        - fc2 -> both actor_head and critic_head (initialize with same weights)
        """
        cql_state = torch.load(path, map_location=self.device)

        # Check if this is a UnifiedNetwork checkpoint (has actor_head/critic_head)
        has_unified_keys = any(k.startswith("actor_head") or k.startswith("critic_head") for k in cql_state.keys())

        if has_unified_keys:
            # Direct load from UnifiedNetwork checkpoint (fine-tuning case)
            missing, unexpected = self.model.load_state_dict(cql_state, strict=False)
            print(f"Loaded UnifiedNetwork weights from {path}")
            if missing:
                print(f"Missing keys: {missing}")
            if unexpected:
                print(f"Unexpected keys: {unexpected}")
        else:
            # Convert from QNetwork format
            new_state = {}
            for k, v in cql_state.items():
                if k.startswith("fc1"):
                    # fc1 -> fc_shared
                    new_key = k.replace("fc1", "fc_shared")
                    new_state[new_key] = v
                elif k.startswith("fc2"):
                    # fc2 -> both actor_head and critic_head
                    actor_key = k.replace("fc2", "actor_head")
                    critic_key = k.replace("fc2", "critic_head")
                    new_state[actor_key] = v
                    new_state[critic_key] = v.clone()  # Clone for critic
                else:
                    # Copy backbone weights directly (conv_in, bn_in, res_blocks)
                    new_state[k] = v

            missing, unexpected = self.model.load_state_dict(new_state, strict=False)
            print(f"Loaded QNetwork weights from {path} (converted to UnifiedNetwork)")
            print(f"Note: actor_head and critic_head initialized with same fc2 weights")
            if missing:
                print(f"Missing keys: {missing}")
            if unexpected:
                print(f"Unexpected keys: {unexpected}")


    def update_critic(self, batch, max_steps=100000):
        """CQL Update using a batch from Critic Buffer."""
        features = batch["features"].to(self.device)
        actions = batch["action"].long().to(self.device)
        targets = batch["reward"].float().to(self.device)
        masks = batch["mask"].float().to(self.device)

        if actions.dim() == 1:
            actions = actions.unsqueeze(1)
        if targets.dim() > 1:
            targets = targets.squeeze()

        # Dynamic CQL alpha scheduling
        progress = min(1.0, self.total_steps / max_steps)
        alpha_cql = self.alpha_cql_init + progress * (self.alpha_cql_final - self.alpha_cql_init)

        self.optimizer.zero_grad()

        _, q_values = self.model(features)
        q_data = q_values.gather(1, actions).squeeze(1)

        # CQL Loss: logsumexp(Q) - Q_data
        invalid_mask = (masks == 0)
        q_masked = q_values.clone()
        q_masked = q_masked.masked_fill(invalid_mask, -1e9)
        logsumexp_q = torch.logsumexp(q_masked, dim=1)
        cql_term = logsumexp_q - q_data

        # MSE Loss
        mse_term = self.mse_loss(q_data, targets)

        # Total Loss
        loss = (mse_term + alpha_cql * cql_term).mean()

        if torch.isnan(loss):
            return {
                "critic/loss": 0.0,
                "critic/cql": 0.0,
                "critic/cql_alpha": alpha_cql,
                "critic/mse": 0.0,
                "critic/q_mean": 0.0,
            }

        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=10.0)
        self.optimizer.step()

        self.total_steps += 1

        return {
            "critic/loss": loss.item(),
            "critic/cql": cql_term.mean().item(),
            "critic/cql_alpha": alpha_cql,
            "critic/mse": mse_term.mean().item(),
            "critic/q_mean": q_data.mean().item(),
        }

    def update_actor(self, batch):
        """
        AWAC (Advantage Weighted Actor-Critic) Update - Off-Policy Learning.
        Batch contains: features, action, reward (G_t), mask.
        No policy version checking needed (off-policy).
        """
        # Get features as tensor (B, 46, 34)
        features = batch["features"].to(self.device)

        actions = batch["action"].long().to(self.device)
        returns = batch["reward"].float().to(self.device) # G_t
        masks = batch["mask"].float().to(self.device)

        if actions.dim() > 1: actions = actions.squeeze(1)
        if returns.dim() > 1: returns = returns.squeeze(1)

        # Advantage Estimation (raw, not normalized for AWAC)
        with torch.no_grad():
            _, q_values = self.model(features)
            q_values = q_values.masked_fill(masks == 0, -1e9)
            values, _ = q_values.max(dim=1) # (B)
            advantages = returns - values

        # Clear gradients before forward pass
        self.optimizer.zero_grad()

        # AWAC: Advantage-weighted policy gradient
        logits, _ = self.model(features)
        logits = logits.masked_fill(masks == 0, -1e9)
        dist = Categorical(logits=logits)

        new_log_probs = dist.log_prob(actions)
        entropy = dist.entropy().mean()

        # AWAC weight: exp(advantage / beta), clamped
        weights = torch.exp(advantages / self.awac_beta)
        weights = torch.clamp(weights, max=self.awac_max_weight)

        # AWAC loss: weighted negative log likelihood
        actor_loss = -(new_log_probs * weights.detach()).mean()
        loss = actor_loss - 0.01 * entropy

        if torch.isnan(loss):
            return {
                "actor/loss": 0.0,
                "actor/entropy": 0.0,
                "actor/advantage": 0.0,
                "actor/awac_weight_mean": 0.0,
            }

        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=10.0)
        self.optimizer.step()

        return {
            "actor/loss": loss.item(),
            "actor/entropy": entropy.item(),
            "actor/advantage": advantages.mean().item(),
            "actor/awac_weight_mean": weights.mean().item(),
        }