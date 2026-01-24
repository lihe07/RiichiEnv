
"""
train_offline.py
Offline RL Baseline using Conservative Q-Learning (CQL).
Trains a Q-function using decayed rewards and CQL regularization to prevent OOD action overestimation.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np
import os
import glob
from offline_dataset import OfflineDataset
from consts import *

# Simple ResNet Block
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

class Phase1Model(nn.Module):
    def __init__(self, in_channels, num_actions, filters=64, blocks=3):
        super().__init__()
        self.conv_in = nn.Conv1d(in_channels, filters, kernel_size=3, padding=1)
        self.bn_in = nn.BatchNorm1d(filters)
        self.relu = nn.ReLU(inplace=True)
        
        self.res_blocks = nn.ModuleList([ResBlock(filters) for _ in range(blocks)])
        
        # Q-Value Head (unnormalized logits)
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(filters * 34, 256)
        self.fc2 = nn.Linear(256, num_actions)
        
    def forward(self, x, mask=None):
        out = self.conv_in(x)
        out = self.bn_in(out)
        out = self.relu(out)
        for block in self.res_blocks:
            out = block(out)
        out = self.flatten(out)
        out = self.relu(self.fc1(out))
        out = self.fc2(out)
        
        # Masking is primarily for Softmax/LogSumExp operations in Loss
        # But we return raw Q-values here. Masking logic moved to loss calculation usually.
        # Or we can apply a large negative value here if mask is provided.
        if mask is not None:
             out = out.masked_fill(~mask, -1e9)
             
        return out

def cql_loss(q_values, current_actions, masks=None, alpha=CQL_ALPHA):
    """
    CQL Loss = MSE(Q(s,a), Target) + alpha * (logsumexp(Q(s, .)) - Q(s, a))
    
    q_values: (B, NumActions)
    current_actions: (B) Indices of expert actions
    masks: (B, NumActions) Boolean mask of legal actions
    """
    # 1. CQL Regularization: maximize Q(s, a_data) - logsumexp(Q(s, a_all))
    # which is equivalent to minimizing logsumexp(Q(s, a_all)) - Q(s, a_data)
    
    # Select Q(s, a_data)
    q_data = q_values.gather(1, current_actions.unsqueeze(1)).squeeze(1) # (B)
    
    # Calculate logsumexp(Q(s, .))
    # If using masks (legal actions only):
    if masks is not None:
        # q_values already masked with -1e9 in forward pass if mask passed.
        # But let's be safe.
        q_masked = q_values.clone()
        q_masked = q_masked.masked_fill(~masks, -1e9)
        logsumexp_q = torch.logsumexp(q_masked, dim=1) # (B)
    else:
        logsumexp_q = torch.logsumexp(q_values, dim=1)
        
    cql_term = (logsumexp_q - q_data).mean()
    
    return cql_term, q_data

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    lr = 1e-4
    batch_size = 32
    
    train_glob = "/data/train.jsonl"
    grp_model = "grp_model.pth"
    
    if len(glob.glob(train_glob)) == 0:
         # Fallback logic for demo/verification
         pass
         
    dataset = OfflineDataset(train_glob, grp_model, device="cpu")
    dataloader = DataLoader(dataset, batch_size=batch_size, num_workers=0)
    
    model = Phase1Model(in_channels=FEATURE_CHANNELS, num_actions=ACTION_SPACE_SIZE).to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    mse_criterion = nn.MSELoss()
    
    model.train()
    
    step = 0
    running_loss = 0.0
    running_cql = 0.0
    running_mse = 0.0
    
    for i, batch in enumerate(dataloader):
        features, actions, rewards, masks = batch
        
        features = features.to(device)
        actions = actions.to(device)
        rewards = rewards.float().to(device)
        masks = masks.to(device)
        
        optimizer.zero_grad()
        
        # Forward with mask to set illegal actions to -inf
        q_values = model(features, mask=masks) 
        
        # CQL Loss
        cql_term, q_data = cql_loss(q_values, actions, masks=masks, alpha=CQL_ALPHA)
        
        # MSE Loss (Monte Carlo Return as target)
        mse_term = mse_criterion(q_data, rewards)
        
        # Combined
        # Mortal uses: 0.5 * MSE + alpha * CQL (if using MC targets?)
        # Let's use simple sum: MSE + alpha * CQL
        loss = mse_term + CQL_ALPHA * cql_term
        
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        running_cql += cql_term.item()
        running_mse += mse_term.item()
        
        if step % 10 == 0:
            print(f"Step {step}, Loss: {running_loss/10:.4f} (MSE: {running_mse/10:.4f}, CQL: {running_cql/10:.4f})")
            running_loss = 0.0
            running_cql = 0.0
            running_mse = 0.0
            
        step += 1
        
    torch.save(model.state_dict(), "offline_cql_model.pth")
    print("Training finished.")

if __name__ == "__main__":
    train()
