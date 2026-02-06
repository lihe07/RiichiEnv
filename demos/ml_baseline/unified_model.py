import torch.nn as nn


class ResBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv1d(channels, channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv1d(channels, channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(channels)

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out += residual
        out = self.relu(out)
        return out


class UnifiedNetwork(nn.Module):
    """Unified Network with CNN backbone for actor-critic architecture."""

    def __init__(self, in_channels=46, num_actions=82, filters=64, blocks=3):
        super().__init__()
        self.conv_in = nn.Conv1d(in_channels, filters, kernel_size=3, padding=1)
        self.bn_in = nn.BatchNorm1d(filters)
        self.relu = nn.ReLU(inplace=True)

        self.res_blocks = nn.ModuleList([ResBlock(filters) for _ in range(blocks)])

        self.flatten = nn.Flatten()

        combined_dim = filters * 34  # 64 * 34 = 2176
        self.fc_shared = nn.Linear(combined_dim, 256)

        # Dual Heads (actor and critic share same fc1, but have separate output heads)
        self.actor_head = nn.Linear(256, num_actions)
        self.critic_head = nn.Linear(256, num_actions)

    def forward(self, x):
        """
        Args:
            x: Tensor (B, 46, 34) spatial features
        """
        spatial = x

        # Process spatial features with CNN
        out = self.conv_in(spatial)
        out = self.bn_in(out)
        out = self.relu(out)
        for block in self.res_blocks:
            out = block(out)

        out = self.flatten(out)  # (B, filters*34 = 2176)

        # Shared layer (match old QNetwork: fc1)
        features = self.relu(self.fc_shared(out))  # (B, 256)

        # Dual heads
        logits = self.actor_head(features)   # (B, 82)
        q_values = self.critic_head(features)  # (B, 82)

        # Returns (logits, q_values)
        return logits, q_values
