from torch import nn, optim, Tensor
import torch


class Dummy(nn.Module):
    def __init__(self, n_classes, match_input_shape=False):
        super().__init__()
        self.name = "Dummy"
        self.num_classes = n_classes
        self.match_input_shape = match_input_shape

        # dummy parameter to satisfy optimizers
        self.dummy = nn.Parameter(torch.zeros(1))

    def forward(self, x):
        if self.match_input_shape:
            return self.dummy * torch.ones(
                x.shape[0], self.num_classes, device=x.device
            )
        return torch.tensor(1.0, device=x.device).expand(())


class DummyModel:
    def __init__(self, n_classes=10):
        self.model = Dummy(n_classes, match_input_shape=True)

    def infer(self, audios: list) -> list:
        batch_size = len(audios)
        dummy_input = torch.zeros(batch_size, 1, 16000)  # Example input shape
        with torch.no_grad():
            outputs = self.model(dummy_input)
        predictions = torch.argmax(outputs, dim=1)
        return list(predictions)


Model = lambda: DummyModel()
