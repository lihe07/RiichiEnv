
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


class ActorNetwork(nn.Module):
    def __init__(self, in_channels=46, num_actions=82, filters=64, blocks=3):
        super().__init__()
        self.conv_in = nn.Conv1d(in_channels, filters, kernel_size=3, padding=1)
        self.bn_in = nn.BatchNorm1d(filters)
        self.relu = nn.ReLU(inplace=True)
        
        self.res_blocks = nn.ModuleList([ResBlock(filters) for _ in range(blocks)])
        
        self.flatten = nn.Flatten()
        
        # Input to FC: filters * 34 (since we don't pool, 34 tiles remain)
        self.fc1 = nn.Linear(filters * 34, 256)
        self.fc2 = nn.Linear(256, num_actions)
        
    def forward(self, x):
        # x: (B, C, 34)
        out = self.conv_in(x)
        out = self.bn_in(out)
        out = self.relu(out)
        for block in self.res_blocks:
            out = block(out)
        
        out = self.flatten(out)
        out = self.relu(self.fc1(out))
        out = self.fc2(out)

        # Returns unnormalized logits
        return out
