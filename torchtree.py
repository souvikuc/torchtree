import torch
from torch import nn
from torchinfo import summary
from torchvision import models
from rich.tree import Tree
from rich import print as rprint
from bigtree import dict_to_tree

from hooks import ModelHooks
from model_info import ModelInfo


class TorchTree:
    """
    A class to manage a tree structure of PyTorch modules.
    """

    def __init__(
        self,
        model_hooks: ModelHooks,
        level: int | tuple = None,
    ):
        self.model_hooks = model_hooks

    @property
    def model(self):
        return self.model_hooks.model

    def get_dummy_inputs(self, input_data=None, input_size=None):
        """
        Returns a dummy input tensor based on the model's input shape.
        Returns:
            A dummy input tensor.
        """
        input_data_specified = (input_data is not None) or (input_size is not None)

        if input_data_specified and input_size is not None:
            return torch.randn(*input_size)
        elif input_data_specified and input_data is not None:
            return input_data
        else:
            raise ValueError("Input data or size must be defined in the model.")


def summary_table(
    model: nn.Module, input_data=None, input_size=None, level: int | tuple = None
):
    model_info = ModelInfo(model)
    model_hooks = ModelHooks(model_info, level)
    model_hooks.register_layer_hooks(model_hooks.layer_info_hook)
    torchtree = TorchTree(model_hooks, level)

    dummy_inputs = torchtree.get_dummy_inputs(input_data, input_size)
    torchtree.model(dummy_inputs)
    model_hooks.remove_hooks()
    # rprint(
    #     model_hooks.layer_info[0].infodict(
    #         "name",
    #         "class_name",
    #     )
    # )


def summary_tree(
    model: nn.Module, input_data=None, input_size=None, level: int | tuple = None
):
    model_info = ModelInfo(model)
    model_hooks = ModelHooks(model_info, level)
    model_hooks.register_layer_hooks(model_hooks.layer_info_hook)
    torchtree = TorchTree(model_hooks, level)

    dummy_inputs = torchtree.get_dummy_inputs(input_data, input_size)
    torchtree.model(dummy_inputs)
    model_hooks.remove_hooks()

    tree_dict = {
        layer.name: layer.infodict("class_name") for layer in model_hooks.layer_info
    }
    root = dict_to_tree(tree_dict, sep=".")
    root.show(attr_list=["class_name"], attr_bracket=("(", ")"))
    # keyf = lambda text: text.split(".")[0]
    # y1 = {i.name for i in model_hooks.layer_info}
    # r = [list(items) for gr, items in groupby(sorted(y1), key=keyf)]


if __name__ == "__main__":

    class ImageMulticlassClassificationNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.conv1 = nn.Conv2d(1, 6, 3)
            self.pool = nn.MaxPool2d(2, 2)
            self.conv2 = nn.Conv2d(6, 16, 3)
            self.flatten = nn.Flatten()
            # self.fc1 = nn.Linear(16 * 11 * 11, 128)  # out: (BS, 128)
            # self.fc2 = nn.Linear(128, 64)
            # self.fc3 = nn.Linear(64, NUM_CLASSES)
            self.relu = nn.ReLU()
            # self.softmax = nn.LogSoftmax()
            self.class_head1 = nn.Sequential(
                nn.Linear(16 * 11 * 11, 128),
                nn.ReLU(),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, 5),
                nn.Softmax(dim=-1),
            )
            self.class_head2 = nn.Sequential(
                nn.Linear(16 * 11 * 11, 128),
                nn.ReLU(),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, 5),
                nn.Softmax(dim=-1),
            )

        def forward(self, x):
            x = self.conv1(x)  # out: (BS, 6, 48, 48)
            x = self.relu(x)
            x = self.pool(x)  # out: (BS, 6, 24, 24)
            x = self.conv2(x)  # out: (BS, 16, 22, 22)
            x = self.relu(x)
            x = self.pool(x)  # out: (BS, 16, 11, 11)
            x = self.flatten(x)
            x1 = self.class_head1(x)  # out: (BS, NUM_CLASSES)
            x2 = self.class_head2(x)  # out: (BS, NUM_CLASSES)
            # x = self.fc1(x)
            # x = self.relu(x)
            # x = self.fc2(x)
            # x = self.relu(x)
            # x = self.fc3(x)
            # x = self.softmax(x)
            return x1, x2

    class Block(nn.Module):
        def __init__(self, in_features, out_features):
            super().__init__()
            self.fc1 = nn.Linear(in_features, 10)
            # self.fc2 = nn.Linear(10, 20)
            self.fc2 = nn.Linear(10, out_features)
            # self.relu = nn.ReLU()

        def forward(self, x):
            return self.fc2(self.fc1(x))

    class NestedModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.block1 = Block(8, 16)
            self.block2 = Block(16, 32)
            self.nested_block = nn.Sequential(Block(32, 64), Block(64, 128))
            self.final_conv = nn.Linear(128, 10)

        def forward(self, x):
            x = self.block1(x)
            x = self.block2(x)
            x = self.nested_block(x)
            x = self.final_conv(x)
            return x

    mymodel = NestedModel()
    # mymodel = models.vgg19(weights=models.VGG19_Weights.DEFAULT)
    # mymodel = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
    # mymodel = ImageMulticlassClassificationNet()
    n = 2
    # summary_table(mymodel, input_size=(1, 3, 512, 512), level=n)
    summary_tree(mymodel, input_size=(1, 8), level=n)

    # y = tt.model_hooks.layer_info[0].infodict(
    #     "name",
    #     "class_name",
    #     "depth",
    #     "parent",
    #     "children",
    #     "input_shape",
    #     "output_shape",
    #     "is_leaf",
    #     "trainable",
    #     "total_params",
    #     "trainable_params",
    #     "non_trainable_params",
    # )
    # rprint(y)
    # summary(
    #     mymodel,
    #     (1, 3, 224, 224),
    #     depth=n,
    #     col_names=[
    #         "input_size",
    #         "output_size",
    #         # "num_params",
    #         # "params_percent",
    #     ],
    #     row_settings=["var_names", "depth"],
    # )
