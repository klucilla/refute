"""Refute's count of the population 2302.12465's evaluator averages over (W3.12f,
docs/validation/v0.3/wp3-population-count-acceptance.md, section 1).

Run in the production container of the claim, in a copy of the repository at commit
cdb7160f9a2fd90bded8cefa8f591f9a0e47ee6c (amazon-science/page-link-path-based-gnn-
explanation), with no network. It reproduces `eval_explanations.py` with the evaluator's
effective arguments in the claims' command (`--dataset_name=synthetic --emb_dim=64
--hidden_dim=64 --out_dim=64`, no `--config_path`, every other argument at its default:
lines 14-55), up to its selection (lines 57-118): the dataset and the split
(`load_dataset`, lines 73-77), the saved model (lines 78-85), the 144 test links (lines
87-92) and, for each, the prediction on its k-hop subgraph, kept when `> 0.5`, keyed by
the pair as `comp_graphs` (lines 94-109). It stops there and prints one line,
`refute-population-count <K>`: the number of distinct pairs kept, the population the
mean of `Average Mask-AUC` is taken over (lines 128-145). It loads no explanation, builds
no mask and computes no AUROC; it reads nothing a run wrote.
"""

from collections import defaultdict

import torch
from data_processing import load_dataset
from model import HeteroLinkPredictionModel, HeteroRGCN
from utils import hetero_src_tgt_khop_in_subgraph

# the evaluator's effective arguments (eval_explanations.py lines 14-55, 60-71)
DATASET_DIR, DATASET_NAME = "datasets", "synthetic"
VALID_RATIO, TEST_RATIO, MAX_NUM_SAMPLES = 0.1, 0.2, -1
EMB_DIM = HIDDEN_DIM = OUT_DIM = 64
SAVED_MODEL_DIR, SAVED_MODEL_NAME = "saved_models", f"{DATASET_NAME}_model"
SRC_NTYPE, TGT_NTYPE, LINK_PRED_OP, NUM_HOPS = "user", "item", "dot", 2

g, processed_g, _, _ = load_dataset(DATASET_DIR, DATASET_NAME, VALID_RATIO, TEST_RATIO)
mp_g, train_pos_g, train_neg_g, val_pos_g, val_neg_g, test_pos_g, test_neg_g = list(processed_g)
encoder = HeteroRGCN(mp_g, EMB_DIM, HIDDEN_DIM, OUT_DIM)
model = HeteroLinkPredictionModel(encoder, SRC_NTYPE, TGT_NTYPE, LINK_PRED_OP)
state = torch.load(f"{SAVED_MODEL_DIR}/{SAVED_MODEL_NAME}.pth", map_location="cpu")
model.load_state_dict(state)

test_src_nids, test_tgt_nids = test_pos_g.edges()
selected = defaultdict(list)
test_ids = range(test_src_nids.shape[0])
if MAX_NUM_SAMPLES > 0:
    test_ids = test_ids[:MAX_NUM_SAMPLES]
for i in test_ids:
    src_nid, tgt_nid = test_src_nids[i], test_tgt_nids[i]
    comp_g_src_nid, comp_g_tgt_nid, comp_g, comp_g_feat_nids = hetero_src_tgt_khop_in_subgraph(
        SRC_NTYPE, src_nid, TGT_NTYPE, tgt_nid, mp_g, NUM_HOPS
    )
    with torch.no_grad():
        pred = (
            model(comp_g_src_nid, comp_g_tgt_nid, comp_g, comp_g_feat_nids).sigmoid().item() > 0.5
        )
    if pred:
        src_tgt = ((SRC_NTYPE, int(src_nid)), (TGT_NTYPE, int(tgt_nid)))
        selected[src_tgt] = [comp_g_src_nid, comp_g_tgt_nid, comp_g, comp_g_feat_nids]

print(f"refute-population-count {len(selected)}", flush=True)
