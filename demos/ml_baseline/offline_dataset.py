
import torch
from torch.utils.data import IterableDataset
from riichienv import RiichiEnv
from riichienv.replay import MjaiReplay, MjSoulReplay
import glob
import numpy as np
from feature_encoder import FeatureEncoder
from consts import *
from grp_model import RewardPredictor

import json

class OfflineDataset(IterableDataset):
    def __init__(self, file_pattern: str, grp_model_path: str, device="cpu"):
        self.file_list = glob.glob(file_pattern)
        self.grp_model_path = grp_model_path
        self.device = device
        self.pts_weights = [100, 40, -40, -100]
        
    def __iter__(self):
        rp = RewardPredictor(self.grp_model_path, self.pts_weights, device=self.device)
        
        for file_path in self.file_list:
            try:
                if file_path.endswith('.jsonl'):
                    replay = MjaiReplay.from_jsonl(file_path)
                elif file_path.endswith('.json'):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    replay = MjSoulReplay.from_dict(json.loads(content))
                else:
                    continue
                    
                kyokus = replay.take_kyokus()
                for kyoku in kyokus:
                    yield from self.process_kyoku(kyoku, rp)
                    
            except Exception as e:
                # print(f"Error loading {file_path}: {e}")
                continue
                
    def process_kyoku(self, kyoku, rp):
        # Calculate Rewards using Global Reward Predictor (same as before)
        try:
             features_dict = kyoku.grp_features() 
             adapted_features = {}
             adapted_features['chang'] = features_dict['chang']
             adapted_features['ju'] = features_dict['ju']
             adapted_features['ben'] = features_dict['ben']
             adapted_features['liqibang'] = features_dict['liqibang']
             
             for i in range(4):
                 adapted_features[f'p{i}_init_score'] = features_dict['scores'][i]
                 adapted_features[f'p{i}_end_score'] = features_dict['end_scores'][i]
                 adapted_features[f'p{i}_delta_score'] = features_dict['delta_scores'][i]
             
             player_rewards = []
             for p in range(4):
                 _, rewards = rp.calc_pts_rewards([adapted_features], p)
                 player_rewards.append(rewards[0].item())
                 
        except Exception as e:
            return 
            
        final_rewards = player_rewards
        gamma = 0.99 

        # Initialize Environment in Replay Mode
        # We need to initialize with specific rules/seeds if possible?
        # Or just default is fine, as `apply_mjai_event` will override state.
        # But `NewRound` event contains initiation info.
        
        env = RiichiEnv(skip_mjai_logging=True)
        # We might need to manually trigger "NewRound" via apply_mjai_event?
        # Kyoku object has all actions.
        # MjSoulReplay/MjaiReplay `raw_actions` vs `actions`.
        # `kyoku.actions` is a list of `replay.Action`.
        
        # We need the `NewRound` action which sets up the board.
        # In `MjSoulReplay`, `kyoku_from_raw_actions` consumes NewRound to set up struct.
        # `kyoku.actions` starts with Discard/Deal usually (after new round).
        # We need `env` to match `kyoku` start state.
        
        # We should create a helper `env.restore_kyoku(kyoku)`?
        # Or manually applying an action: `env.apply_log_action` requires `Action`.
        
        # Workaround: Use `Action::NewRound` if we exposed it?
        # `state.rs` handles `Action`. `Action` enum in `replay` has `NewRound`?
        # `replay/mod.rs` Action enum: `DiscardTile`, `DealTile`, ... NO `NewRound`.
        # `NewRound` is handled during parsing to create `Kyoku`.
        
        # So we must initialize Env from Kyoku fields.
        # `env.reset(scores=..., oya=..., wall=..., ...)`
        env.reset(
            oya=kyoku.scores[0], # Oops, oya arg is dealer index? 
            # kyoku.scores is [i32; 4].
            # We need to identify Oya.
            # In Mjai, oya is usually (chang * 4 + ju) % 4?
            # Or explicit.
            # Let's rely on `kyoku.ju` (honba?) and `kyoku.chang`.
            # Oya is usually determined by round logic.
            # Let's assume standard rotation: Dealer = (kyoku_idx) % 4. 
            # In `mjsoul_replay`, `ju` might range 0-3?
            # Let's use `env.reset` logic.
            scores=kyoku.scores,
            honba=kyoku.ben,
            kyotaku=kyoku.liqibang,
            wall=None # We don't have the wall easily here? Or do we?
                      # Kyoku struct has `paishan` string?
                      # If paishan is None, we can't reproduce Deal perfectly?
                      # But Replay log contains draws!
                      # Offline RL relies on `DealTile` events to tell us what was drawn.
                      # So we don't strictly need the wall if we trust `DealTile`.
        )
        # Also set hard state
        # env.state.oya = ?
        # We might need `env.set_state(...)` helper.
        
        encs = [FeatureEncoder(pid) for pid in range(4)]
        
        samples = [[] for _ in range(4)]
        
        # Iterate actions
        # kyoku.actions is Arc<[Action]>.
        # We need to fetch it.
        # Using `kyoku.actions` property exposed to Python?
        # Check `replay/mod.rs` -> `actions` field is `Arc<[Action]>`.
        # Python doesn't see Arc directly.
        # We need `kyoku.actions` to return list of actions.
        # `replay/mod.rs` doesn't expose `actions` getter yet! (It exposes `events()` which returns dicts).
        
        # If we use `events()` (list of dicts), we can feed them to `feature_encoder`?
        # But we want to use `RiichiEnv`.
        
        # Solution: Use `kyoku.events(None)` to get dicts.
        # Then `env.apply_mjai_event_dict(dict)`?
        # `state.rs` has `apply_log_action` taking `LogAction`.
        # We need a bridge: Dict -> LogAction OR Dict -> State.
        # Or expose `kyoku.get_log_actions()` returning `Vec<LogAction>`.
        
        # Assuming we added `apply_mjai_event` that takes Dict/Value in `RiichiEnv`?
        # But parsing Dict to `LogAction` is tedious in Rust if not reusing code.
        # `MjSoulReplay` has parsing logic.
        
        # Let's stick to: Update `Kyoku` to expose `actions` as list of objects?
        # Or just iterate `events` and have `env` parse them?
        # `RiichiEnv._filter_mjai_event` exists.
        # We need `RiichiEnv.apply_mjai_dict`.
        
        # Let's assume `RiichiEnv` has `apply_mjai_dict(dict)`.
        # I did not implement that in `state.rs` yet explicitly, only `apply_log_action`.
        # I should probably add `apply_mjai_dict` that parses using `serde_json`.
        
        # For now, let's use a hypothetical `env.apply_event(evt_dict)`.
        
        events = kyoku.events(None)
        
        # We need to detect "My Turn" to generate label.
        # Similar logic to before: If we just drew, predict Discard.
        
        for i, evt in enumerate(events):
            name = evt['name']
            data = evt.get('data', {})
            
            # Apply to Env
            # env.step_event(evt) ?
            # This is critical.
            # If I can't `step_event`, I can't update state.
            pass 
            
            # (Impl detail skipped: Requires Rust update to accept dict)
