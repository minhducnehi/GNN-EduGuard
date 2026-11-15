import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import HGTConv

class FocalLoss(nn.Module):
    """
    Focal Loss with class weights for imbalanced student risk classification.
    Prioritizes hard examples and boosts Recall on the minority at-risk class.
    """
    def __init__(self, weight: torch.Tensor = None, alpha: float = 0.65, gamma: float = 2.0):
        super().__init__()
        self.register_buffer("weight", weight)
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        ce_loss = F.cross_entropy(logits, targets, weight=self.weight, reduction="none")
        pt = torch.exp(-ce_loss)
        alpha_t = torch.where(targets == 1, self.alpha, 1.0 - self.alpha)
        focal_loss = alpha_t * ((1.0 - pt) ** self.gamma) * ce_loss
        return focal_loss.mean()


class StudentRiskHGT(nn.Module):
    """
    Heterogeneous Graph Transformer (HGT) with Residual Connections & LayerNorm
    for Early Student Academic Risk Prediction.
    """
    def __init__(
        self,
        in_dims: dict,
        metadata: tuple,
        hidden_channels: int = 64,
        num_heads: int = 4,
        num_layers: int = 2,
        dropout: float = 0.25
    ):
        super().__init__()
        self.hidden_channels = hidden_channels
        self.dropout = dropout
        node_types = metadata[0]

        # Node-type specific input projections
        self.input_proj = nn.ModuleDict({
            nt: nn.Sequential(
                nn.Linear(in_dims[nt], hidden_channels),
                nn.LayerNorm(hidden_channels),
                nn.GELU()
            )
            for nt in node_types
        })

        # HGT Message Passing Layers
        self.convs = nn.ModuleList([
            HGTConv(
                in_channels=hidden_channels,
                out_channels=hidden_channels,
                metadata=metadata,
                heads=num_heads
            )
            for _ in range(num_layers)
        ])

        self.norms = nn.ModuleList([
            nn.ModuleDict({nt: nn.LayerNorm(hidden_channels) for nt in node_types})
            for _ in range(num_layers)
        ])

        # Classification head combining initial student representation + GNN-enriched representation
        self.classifier = nn.Sequential(
            nn.Linear(hidden_channels * 2, hidden_channels),
            nn.LayerNorm(hidden_channels),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_channels, 2)
        )

    def forward(self, x_dict: dict, edge_index_dict: dict, return_embeddings: bool = False):
        h_init = {
            nt: proj(x_dict[nt])
            for nt, proj in self.input_proj.items()
        }
        h_dict = {nt: h.clone() for nt, h in h_init.items()}

        for conv, norm_dict in zip(self.convs, self.norms):
            out_dict = conv(h_dict, edge_index_dict)
            next_h = {}
            for nt in h_dict.keys():
                if nt in out_dict and out_dict[nt] is not None:
                    updated = F.dropout(F.gelu(out_dict[nt]), p=self.dropout, training=self.training)
                    next_h[nt] = norm_dict[nt](h_dict[nt] + updated)
                else:
                    next_h[nt] = h_dict[nt]
            h_dict = next_h

        # Concatenate initial node embedding and multi-hop graph embedding for student nodes
        student_repr = torch.cat([h_init["student"], h_dict["student"]], dim=-1)
        logits = self.classifier(student_repr)

        if return_embeddings:
            return logits, h_dict
        return logits
