import argparse
import glob
import os

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
import numpy as np

import wandb
from dotenv import load_dotenv
load_dotenv()

from cql_dataset import MCDataset, TransitionDataset
from cql_model import QNetwork
from grp_model import RewardPredictor
from utils import AverageMeter


def cql_loss(q_values, current_actions, masks=None):
    """
    Computes CQL Regularization Term: logsumexp(Q(s, a_all)) - Q(s, a_data)
    """
    # q_values: (B, NumActions)
    # current_actions: (B) index
    
    # 1. Q(s, a_data)
    # actions is (B), unsqueeze to (B,1), gather, squeeze -> (B)
    q_data = q_values.gather(1, current_actions.unsqueeze(1)).squeeze(1)
    
    # 2. logsumexp(Q(s, .))
    if masks is not None:
        # Mask invalid actions with -inf before logsumexp
        # masks is 1.0 for valid, 0.0 for invalid? 
        # get_legal_action_mask returns 1.0 for valid.
        # We need Boolean mask where True = keep (valid).
        # masked_fill takes mask where True = fill.
        # So we want mask where True = INVALID.
        # masks tensor is 1.0 (valid).
        invalid_mask = (masks < 0.5)
        q_masked = q_values.clone()
        q_masked = q_masked.masked_fill(invalid_mask, -1e9)
        logsumexp_q = torch.logsumexp(q_masked, dim=1)
    else:
        logsumexp_q = torch.logsumexp(q_values, dim=1)

    cql_term = (logsumexp_q - q_data).mean()
    return cql_term, q_data


def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Initialize Reward Predictor
    pts_weight = [10.0, 4.0, -4.0, -10.0]
    reward_predictor = RewardPredictor(args.grp_model, pts_weight, device=str(device), input_dim=20)

    # Dataset
    data_files = glob.glob(args.data_glob)
    if not data_files:
        print(f"No data found at {args.data_glob}")
        return

    print(f"Found {len(data_files)} data files.")    
    dataset = MCDataset(data_files, reward_predictor, gamma=args.gamma)        
    dataloader = DataLoader(dataset, batch_size=args.batch_size, num_workers=8)

    # Model
    model = QNetwork(in_channels=46, num_actions=82).to(device)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.limit, eta_min=1e-7)
    mse_criterion = nn.MSELoss()
    model.train()
    
    step = 0
    run = wandb.init(
        entity="smly",
        project="riichienv-mc-cql",
        config={
            "learning_rate": args.lr,
            "batch_size": args.batch_size,
            "gamma": args.gamma,
            "alpha": args.alpha,
            "dataset": args.data_glob,
        },
    )

    loss_meter = AverageMeter(name="loss")
    cql_meter = AverageMeter(name="cql")
    mse_meter = AverageMeter(name="mse")

    for epoch in range(args.num_epochs):
        for i, batch in enumerate(dataloader):
            # (feat, act, return, mask)
            features, actions, targets, masks = batch
            next_features = None
            dones = None
            # targets is G_t

            features = features.to(device)
            actions = actions.long().to(device)
            targets = targets.float().to(device)
            masks = masks.float().to(device)
            
            optimizer.zero_grad()
            
            # 1. Compute Q(s, a)
            q_values = model(features)
            
            # 2. CQL Loss
            cql_term, q_data = cql_loss(q_values, actions, masks)
            
            # 3. Bellman Error
            # Regression to G_t
            # targets is (B, 1), q_data is (B). Squeeze targets.
            mse_term = mse_criterion(q_data, targets.squeeze(-1))

            # Total Loss
            loss = mse_term + args.alpha * cql_term
            
            loss.backward()
            optimizer.step()

            loss_meter.update(loss.item())
            cql_meter.update(cql_term.item())
            mse_meter.update(mse_term.item())
            
            if step % 100 == 0:
                print(f"Epoch {epoch}, Step {step}, Loss: {loss_meter.avg:.4f} (MSE: {mse_meter.avg:.4f}, CQL: {cql_meter.avg:.4f})")
                run.log({
                    "epoch": epoch,
                    "loss": loss_meter.avg,
                    "mse": mse_meter.avg,
                    "cql": cql_meter.avg,
                }, step=step)

            step += 1
            scheduler.step()

        loss_meter.reset()
        cql_meter.reset()
        mse_meter.reset()

        torch.save(model.state_dict(), args.output)
        print(f"Saved model to {args.output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_glob", type=str, required=True, help="Glob path for training data (.xz)")
    parser.add_argument("--grp_model", type=str, default="./grp_model.pth", help="Path to reward model")
    parser.add_argument("--output", type=str, default="cql_model.pth", help="Output model path")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--alpha", type=float, default=1.0, help="CQL Scale")
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--num_epochs", type=int, default=10)
    parser.add_argument("--limit", type=int, default=1e6)

    args = parser.parse_args()
    train(args)
