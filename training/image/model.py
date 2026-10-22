"""Original prompt-conditioned diffusion denoiser prototype.

This defines trainable architecture only. It is randomly initialized and has
not been trained. It is not a usable image generator until a proper licensed
image-text dataset, text conditioning, diffusion training loop, sampling
algorithm, and evaluation are implemented and run.
"""
from __future__ import annotations

import torch
from torch import nn


class TimeEmbedding(nn.Module):
    def __init__(self, width: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(1, width), nn.SiLU(), nn.Linear(width, width)
        )

    def forward(self, timestep: torch.Tensor) -> torch.Tensor:
        return self.net(timestep.float().reshape(-1, 1) / 1000.0)


class ConditionalResidualBlock(nn.Module):
    def __init__(self, channels: int, condition_width: int) -> None:
        super().__init__()
        self.norm1 = nn.GroupNorm(8 if channels % 8 == 0 else 1, channels)
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1)
        self.norm2 = nn.GroupNorm(8 if channels % 8 == 0 else 1, channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1)
        self.condition = nn.Linear(condition_width, channels * 2)
        self.activation = nn.SiLU()

    def forward(self, x: torch.Tensor, condition: torch.Tensor) -> torch.Tensor:
        h = self.conv1(self.activation(self.norm1(x)))
        scale, shift = self.condition(condition).chunk(2, dim=-1)
        h = self.norm2(h)
        h = h * (1.0 + scale[:, :, None, None]) + shift[:, :, None, None]
        h = self.conv2(self.activation(h))
        return x + h


class RCConditionalDenoiser(nn.Module):
    """Tiny low-resolution epsilon-predictor, initialized from scratch.

    Inputs:
      noisy_image: [batch, image_channels, height, width]
      timestep: [batch] integer diffusion steps
      text_condition: [batch, condition_width] from a separately trained
        original text encoder; no text encoder is included or pretrained here.
    """
    def __init__(
        self,
        image_channels: int = 3,
        width: int = 32,
        condition_width: int = 128,
    ) -> None:
        super().__init__()
        if width < 8:
            raise ValueError("width must be at least 8")
        self.time = TimeEmbedding(condition_width)
        self.input = nn.Conv2d(image_channels, width, 3, padding=1)
        self.blocks = nn.ModuleList([
            ConditionalResidualBlock(width, condition_width) for _ in range(3)
        ])
        self.output_norm = nn.GroupNorm(8 if width % 8 == 0 else 1, width)
        self.output = nn.Conv2d(width, image_channels, 3, padding=1)
        self.condition_mix = nn.Linear(condition_width, condition_width)

    def forward(
        self,
        noisy_image: torch.Tensor,
        timestep: torch.Tensor,
        text_condition: torch.Tensor,
    ) -> torch.Tensor:
        if noisy_image.ndim != 4:
            raise ValueError("noisy_image must have shape [B,C,H,W]")
        if text_condition.ndim != 2 or text_condition.shape[0] != noisy_image.shape[0]:
            raise ValueError("text_condition must have shape [B,condition_width]")
        if timestep.reshape(-1).shape[0] != noisy_image.shape[0]:
            raise ValueError("timestep batch size must match image batch size")
        condition = self.condition_mix(text_condition) + self.time(timestep)
        x = self.input(noisy_image)
        for block in self.blocks:
            x = block(x, condition)
        return self.output(self.activation(self.output_norm(x))) if hasattr(self, "activation") else self.output(torch.nn.functional.silu(self.output_norm(x)))
