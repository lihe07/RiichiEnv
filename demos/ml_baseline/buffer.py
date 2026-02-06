import torch
import numpy as np
from torchrl.data import TensorDictReplayBuffer, LazyTensorStorage
from torchrl.data.replay_buffers.samplers import SamplerWithoutReplacement
from tensordict import TensorDict


class GlobalReplayBuffer:
    def __init__(self,
                 actor_capacity: int = 50000,
                 critic_capacity: int = 1000000,
                 batch_size: int = 32,
                 device: str = "cpu"):

        self.device = torch.device(device)
        self.batch_size = batch_size

        # Actor Buffer (FIFO / Sliding Window)
        self.actor_buffer = TensorDictReplayBuffer(
            storage=LazyTensorStorage(actor_capacity),
            sampler=SamplerWithoutReplacement(),
        )

        # Critic Buffer (Standard Replay Buffer)
        self.critic_buffer = TensorDictReplayBuffer(
            storage=LazyTensorStorage(critic_capacity),
            sampler=SamplerWithoutReplacement(),
        )

    def add(self, transitions: list[dict]):
        """Adds a list of transitions to both buffers."""
        if not transitions:
            return

        batch_size = len(transitions)

        features = np.stack([t["features"] for t in transitions])

        batch_data = {
            "mask": np.stack([t["mask"] for t in transitions]),
            "action": np.array([t["action"] for t in transitions]),
            "reward": np.array([t["reward"] for t in transitions]),
            "done": np.array([t["done"] for t in transitions], dtype=bool),
            "log_prob": np.array([t["log_prob"] for t in transitions]),
        }

        batch = TensorDict({
            "features": torch.from_numpy(features),
            "mask": torch.from_numpy(batch_data["mask"]),
            "action": torch.from_numpy(batch_data["action"]),
            "reward": torch.from_numpy(batch_data["reward"]),
            "done": torch.from_numpy(batch_data["done"]),
            "log_prob": torch.from_numpy(batch_data["log_prob"]),
        }, batch_size=[batch_size])

        self.actor_buffer.extend(batch)
        self.critic_buffer.extend(batch)

    def sample_actor(self, batch_size=None):
        """Sample from recent data."""
        if batch_size is None:
            batch_size = self.batch_size
        return self.actor_buffer.sample(batch_size=batch_size).to(self.device)

    def sample_critic(self, batch_size=None):
        """Sample from historical data (CQL)."""
        if batch_size is None:
            batch_size = self.batch_size
        return self.critic_buffer.sample(batch_size=batch_size).to(self.device)
