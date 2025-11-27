from torch import nn, optim, Tensor

class DummyModel(nn.Module):
    def __init__(self, n_classes, match_input_shape=False):
        super().__init__()
        self.name = "Dummy"
        self.num_classes = n_classes
        self.match_input_shape = match_input_shape

        # dummy parameter to satisfy optimizers
        self.dummy = nn.Parameter(torch.zeros(1))

    def forward(self, x):
        if self.match_input_shape:
            return self.dummy * torch.ones(x.shape[0], self.num_classes, device=x.device)
        return torch.tensor(1.0, device=x.device).expand(())


ModelBuilder = lambda: DummyModel(2)
