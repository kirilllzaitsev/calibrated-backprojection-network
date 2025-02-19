"""
Author: Alex Wong <alexw@cs.ucla.edu>

If you use this code, please cite the following paper:

A. Wong, and S. Soatto. Unsupervised Depth Completion with Calibrated Backprojection Layers.
https://arxiv.org/pdf/2108.10531.pdf

@inproceedings{wong2021unsupervised,
  title={Unsupervised Depth Completion with Calibrated Backprojection Layers},
  author={Wong, Alex and Soatto, Stefano},
  booktitle={Proceedings of the IEEE/CVF International Conference on Computer Vision},
  pages={12747--12756},
  year={2021}
}
"""
import torch
from kbnet import net_utils


"""
Encoder architectures
"""


class KBNetEncoder(torch.nn.Module):
    """
    Calibrated backprojection network (KBNet) encoder with skip connections

    Arg(s):
        in_channels_image : int
            number of input channels for image (RGB) branch
        in_channels_depth : int
            number of input channels for depth branch
        n_filters_image : int
            number of filters for image (RGB) branch for each KB layer
         n_filters_depth : int
            number of filters for depth branch  for each KB layer
        n_filters_fused : int
            number of filters for RGB 3D fusion branch  for each KB layer
        n_convolution_image : list[int]
            number of convolution layers in image branch  for each KB layer
        n_convolution_depth : list[int]
            number of convolution layers in depth branch  for each KB layer
        n_convolution_fused : list[int]
            number of convolution layers in RGB 3D fusion branch  for each KB layer
        resolutions_backprojection : list[int]
            resolutions at which to use calibrated backprojection layers
        weight_initializer : str
            kaiming_normal, kaiming_uniform, xavier_normal, xavier_uniform
        activation_func : func
            activation function after convolution
    """

    def __init__(
        self,
        input_channels_image=3,
        input_channels_depth=1,
        n_filters_image=[48, 96, 192, 384, 384],
        n_filters_depth=[16, 32, 64, 128, 128],
        n_filters_fused=[48, 96, 192, 384, 384],
        n_convolutions_image=[1, 1, 1, 1, 1],
        n_convolutions_depth=[1, 1, 1, 1, 1],
        n_convolutions_fused=[1, 1, 1, 1, 1],
        resolutions_backprojection=[0, 1, 2],
        weight_initializer="kaiming_uniform",
        activation_func="leaky_relu",
    ):
        super(KBNetEncoder, self).__init__()

        self.resolutions_backprojection = resolutions_backprojection

        network_depth = 5

        assert len(n_convolutions_image) == network_depth
        assert len(n_convolutions_depth) == network_depth
        assert len(n_convolutions_fused) == network_depth
        assert len(n_filters_image) == network_depth
        assert len(n_filters_depth) == network_depth
        assert len(n_filters_fused) == network_depth

        activation_func = net_utils.activation_func(activation_func)

        # Resolution: 1/1 -> 1/2
        n = 0

        if n in resolutions_backprojection:
            # Initial feature extractors on inputs
            self.conv0_image = net_utils.Conv2d(
                in_channels=input_channels_image,
                out_channels=n_filters_image[n],
                kernel_size=3,
                stride=1,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )

            self.conv0_depth = net_utils.Conv2d(
                in_channels=input_channels_depth,
                out_channels=n_filters_depth[n],
                kernel_size=3,
                stride=1,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )

            in_channels_image = n_filters_image[n]
            in_channels_depth = n_filters_depth[n]
            in_channels_fused = n_filters_image[n]

            self.calibrated_backprojection1 = net_utils.CalibratedBackprojectionBlock(
                in_channels_image=in_channels_image,
                in_channels_depth=in_channels_depth,
                in_channels_fused=in_channels_fused,
                n_filter_image=n_filters_image[n],
                n_filter_depth=n_filters_depth[n],
                n_filter_fused=n_filters_fused[n],
                n_convolution_image=n_convolutions_image[n],
                n_convolution_depth=n_convolutions_depth[n],
                n_convolution_fused=n_convolutions_fused[n],
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )
        else:
            self.conv1_image = net_utils.VGGNetBlock(
                in_channels=input_channels_image,
                out_channels=n_filters_image[n],
                n_convolution=n_convolutions_image[n],
                stride=2,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )

            self.conv1_depth = net_utils.VGGNetBlock(
                in_channels=input_channels_depth,
                out_channels=n_filters_depth[n],
                n_convolution=n_convolutions_depth[n],
                stride=2,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )

        # Resolution: 1/2 -> 1/4
        n = 1

        in_channels_image = n_filters_image[n - 1]
        in_channels_depth = n_filters_depth[n - 1]

        if n in resolutions_backprojection:
            if n - 1 in resolutions_backprojection:
                in_channels_fused = n_filters_image[n - 1] + n_filters_fused[n - 1]
            else:
                in_channels_fused = n_filters_image[n - 1]

            self.calibrated_backprojection2 = net_utils.CalibratedBackprojectionBlock(
                in_channels_image=in_channels_image,
                in_channels_depth=in_channels_depth,
                in_channels_fused=in_channels_fused,
                n_filter_image=n_filters_image[n],
                n_filter_depth=n_filters_depth[n],
                n_filter_fused=n_filters_fused[n],
                n_convolution_image=n_convolutions_image[n],
                n_convolution_depth=n_convolutions_depth[n],
                n_convolution_fused=n_convolutions_fused[n],
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )
        else:
            self.conv2_image = net_utils.VGGNetBlock(
                in_channels=in_channels_image,
                out_channels=n_filters_image[n],
                n_convolution=n_convolutions_image[n],
                stride=2,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )

            self.conv2_depth = net_utils.VGGNetBlock(
                in_channels=in_channels_depth,
                out_channels=n_filters_depth[n],
                n_convolution=n_convolutions_depth[n],
                stride=2,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )

        # Resolution: 1/4 -> 1/8
        n = 2

        in_channels_image = n_filters_image[n - 1]
        in_channels_depth = n_filters_depth[n - 1]

        if n in resolutions_backprojection:
            if n - 1 in resolutions_backprojection:
                in_channels_fused = n_filters_image[n - 1] + n_filters_fused[n - 1]
            else:
                in_channels_fused = n_filters_image[n - 1]

            self.calibrated_backprojection3 = net_utils.CalibratedBackprojectionBlock(
                in_channels_image=in_channels_image,
                in_channels_depth=in_channels_depth,
                in_channels_fused=in_channels_fused,
                n_filter_image=n_filters_image[n],
                n_filter_depth=n_filters_depth[n],
                n_filter_fused=n_filters_fused[n],
                n_convolution_image=n_convolutions_image[n],
                n_convolution_depth=n_convolutions_depth[n],
                n_convolution_fused=n_convolutions_fused[n],
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )
        else:
            self.conv3_image = net_utils.VGGNetBlock(
                in_channels=in_channels_image,
                out_channels=n_filters_image[n],
                n_convolution=n_convolutions_image[n],
                stride=2,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )

            self.conv3_depth = net_utils.VGGNetBlock(
                in_channels=in_channels_depth,
                out_channels=n_filters_depth[n],
                n_convolution=n_convolutions_depth[n],
                stride=2,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )

        # Resolution: 1/8 -> 1/16
        n = 3

        in_channels_image = n_filters_image[n - 1]
        in_channels_depth = n_filters_depth[n - 1]

        if n in resolutions_backprojection:
            if n - 1 in resolutions_backprojection:
                in_channels_fused = n_filters_image[n - 1] + n_filters_fused[n - 1]
            else:
                in_channels_fused = n_filters_image[n - 1]

            self.calibrated_backprojection4 = net_utils.CalibratedBackprojectionBlock(
                in_channels_image=in_channels_image,
                in_channels_depth=in_channels_depth,
                in_channels_fused=in_channels_fused,
                n_filter_image=n_filters_image[n],
                n_filter_depth=n_filters_depth[n],
                n_filter_fused=n_filters_fused[n],
                n_convolution_image=n_convolutions_image[n],
                n_convolution_depth=n_convolutions_depth[n],
                n_convolution_fused=n_convolutions_fused[n],
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )
        else:
            self.conv4_image = net_utils.VGGNetBlock(
                in_channels=in_channels_image,
                out_channels=n_filters_image[n],
                n_convolution=n_convolutions_image[n],
                stride=2,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )

            self.conv4_depth = net_utils.VGGNetBlock(
                in_channels=in_channels_depth,
                out_channels=n_filters_depth[n],
                n_convolution=n_convolutions_depth[n],
                stride=2,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )

        # Resolution: 1/16 -> 1/32
        n = 4

        in_channels_image = n_filters_image[n - 1]
        in_channels_depth = n_filters_depth[n - 1]

        if n in resolutions_backprojection:
            if n - 1 in resolutions_backprojection:
                in_channels_fused = n_filters_image[n - 1] + n_filters_fused[n - 1]
            else:
                in_channels_fused = n_filters_image[n - 1]

            self.calibrated_backprojection5 = net_utils.CalibratedBackprojectionBlock(
                in_channels_image=in_channels_image,
                in_channels_depth=in_channels_depth,
                in_channels_fused=in_channels_fused,
                n_filter_image=n_filters_image[n],
                n_filter_depth=n_filters_depth[n],
                n_filter_fused=n_filters_fused[n],
                n_convolution_image=n_convolutions_image[n],
                n_convolution_depth=n_convolutions_depth[n],
                n_convolution_fused=n_convolutions_fused[n],
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )
        else:
            self.conv5_image = net_utils.VGGNetBlock(
                in_channels=in_channels_image,
                out_channels=n_filters_image[n],
                n_convolution=n_convolutions_image[n],
                stride=2,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )

            self.conv5_depth = net_utils.VGGNetBlock(
                in_channels=in_channels_depth,
                out_channels=n_filters_depth[n],
                n_convolution=n_convolutions_depth[n],
                stride=2,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
            )

    def forward(self, image, depth, intrinsics):
        """
        Forward image, depth and calibration through encoder

        Arg(s):
            image : torch.Tensor[float32]
                N x C x H x W image
            depth : torch.Tensor[float32]
                N x 1 x H x W depth map
            intrinsics : torch.Tensor[float32]
                N x C x 3 x 3 calibration
        Returns:
            torch.Tensor[float32] : N x K x h x w output tensor
            list[torch.Tensor[float32]] : list of skip connections
        """

        def camera_coordinates(batch, height, width, k):
            # Reshape pixel coordinates to N x 3 x (H x W)
            xy_h = net_utils.meshgrid(
                n_batch=batch,
                n_height=height,
                n_width=width,
                device=k.device,
                homogeneous=True,
            )
            xy_h = xy_h.view(batch, 3, -1)

            # K^-1 [x, y, 1] z and reshape back to N x 3 x H x W
            coordinates = torch.matmul(torch.inverse(k), xy_h)
            coordinates = coordinates.view(n_batch, 3, height, width)

            return coordinates

        def scale_intrinsics(batch, height0, width0, height1, width1, k):
            device = k.device

            width0 = torch.tensor(width0, dtype=torch.float32, device=device)
            height0 = torch.tensor(height0, dtype=torch.float32, device=device)
            width1 = torch.tensor(width1, dtype=torch.float32, device=device)
            height1 = torch.tensor(height1, dtype=torch.float32, device=device)

            # Get scale in x, y components
            scale_x = n_width1 / n_width0
            scale_y = n_height1 / n_height0

            # Prepare 3 x 3 matrix to do element-wise scaling
            scale = torch.tensor(
                [[scale_x, 1.0, scale_x], [1.0, scale_y, scale_y], [1.0, 1.0, 1.0]],
                dtype=torch.float32,
                device=device,
            )

            scale = scale.view(1, 3, 3).repeat(n_batch, 1, 1)

            return k * scale

        layers = []

        # Resolution: 1/1 -> 1/2
        if 0 in self.resolutions_backprojection:
            n_batch, _, n_height0, n_width0 = image.shape

            # Normalized camera coordinates
            coordinates0 = camera_coordinates(n_batch, n_height0, n_width0, intrinsics)

            # Feature extractors
            conv0_image = self.conv0_image(image)
            conv0_depth = self.conv0_depth(depth)

            # Calibrated backprojection
            conv1_image, conv1_depth, conv1_fused = self.calibrated_backprojection1(
                image=conv0_image,
                depth=conv0_depth,
                coordinates=coordinates0,
                fused=None,
            )

            skips1 = [conv1_fused, conv1_depth]
        else:
            conv1_image = self.conv1_image(image)
            conv1_depth = self.conv1_depth(depth)
            conv1_fused = None

            skips1 = [conv1_image, conv1_depth]

        # Store as skip connection
        layers.append(torch.cat(skips1, dim=1))

        # Resolution: 1/2 -> 1/4
        _, _, n_height1, n_width1 = conv1_image.shape

        if 1 in self.resolutions_backprojection:
            intrinsics1 = scale_intrinsics(
                batch=n_batch,
                height0=n_height0,
                width0=n_width0,
                height1=n_height1,
                width1=n_width1,
                k=intrinsics,
            )

            # Normalized camera coordinates
            coordinates1 = camera_coordinates(n_batch, n_height1, n_width1, intrinsics1)

            # Calibrated backprojection
            conv2_image, conv2_depth, conv2_fused = self.calibrated_backprojection2(
                image=conv1_image,
                depth=conv1_depth,
                coordinates=coordinates1,
                fused=conv1_fused,
            )

            skips2 = [conv2_fused, conv2_depth]
        else:
            if conv1_fused is not None:
                conv2_image = self.conv2_image(conv1_fused)
            else:
                conv2_image = self.conv2_image(conv1_image)

            conv2_depth = self.conv2_depth(conv1_depth)
            conv2_fused = None

            skips2 = [conv2_image, conv2_depth]

        # Store as skip connection
        layers.append(torch.cat(skips2, dim=1))

        # Resolution: 1/4 -> 1/8
        _, _, n_height2, n_width2 = conv2_image.shape

        if 2 in self.resolutions_backprojection:
            intrinsics2 = scale_intrinsics(
                batch=n_batch,
                height0=n_height0,
                width0=n_width0,
                height1=n_height2,
                width1=n_width2,
                k=intrinsics,
            )

            # Normalized camera coordinates
            coordinates2 = camera_coordinates(n_batch, n_height2, n_width2, intrinsics2)

            # Calibrated backprojection
            conv3_image, conv3_depth, conv3_fused = self.calibrated_backprojection3(
                image=conv2_image,
                depth=conv2_depth,
                coordinates=coordinates2,
                fused=conv2_fused,
            )

            skips3 = [conv3_fused, conv3_depth]
        else:
            if conv2_fused is not None:
                conv3_image = self.conv3_image(conv2_fused)
            else:
                conv3_image = self.conv3_image(conv2_image)

            conv3_depth = self.conv3_depth(conv2_depth)
            conv3_fused = None

            skips3 = [conv3_image, conv3_depth]

        # Store as skip connection
        layers.append(torch.cat(skips3, dim=1))

        # Resolution: 1/8 -> 1/16
        _, _, n_height3, n_width3 = conv3_image.shape

        if 3 in self.resolutions_backprojection:
            intrinsics3 = scale_intrinsics(
                batch=n_batch,
                height0=n_height0,
                width0=n_width0,
                height1=n_height3,
                width1=n_width3,
                k=intrinsics,
            )

            # Normalized camera coordinates
            coordinates3 = camera_coordinates(n_batch, n_height3, n_width3, intrinsics3)

            # Calibrated backprojection
            conv4_image, conv4_depth, conv4_fused = self.calibrated_backprojection4(
                image=conv3_image,
                depth=conv3_depth,
                coordinates=coordinates3,
                fused=conv3_fused,
            )

            skips4 = [conv4_fused, conv4_depth]
        else:
            if conv3_fused is not None:
                conv4_image = self.conv4_image(conv3_fused)
            else:
                conv4_image = self.conv4_image(conv3_image)

            conv4_depth = self.conv4_depth(conv3_depth)
            conv4_fused = None

            skips4 = [conv4_image, conv4_depth]

        # Store as skip connection
        layers.append(torch.cat(skips4, dim=1))

        # Resolution: 1/16 -> 1/32
        _, _, n_height4, n_width4 = conv4_image.shape

        if 4 in self.resolutions_backprojection:
            intrinsics4 = scale_intrinsics(
                batch=n_batch,
                height0=n_height0,
                width0=n_width0,
                height1=n_height4,
                width1=n_width4,
                k=intrinsics,
            )

            # Normalized camera coordinates
            coordinates4 = camera_coordinates(n_batch, n_height4, n_width4, intrinsics4)

            # Calibrated backprojection
            conv5_image, conv5_depth, conv5_fused = self.calibrated_backprojection4(
                image=conv4_image,
                depth=conv4_depth,
                coordinates=coordinates4,
                fused=conv4_fused,
            )

            skips5 = [conv5_fused, conv5_depth]
        else:
            if conv4_fused is not None:
                conv5_image = self.conv5_image(conv4_fused)
            else:
                conv5_image = self.conv5_image(conv4_image)

            conv5_depth = self.conv5_depth(conv4_depth)
            conv5_fused = None

            skips5 = [conv5_image, conv5_depth]

        # Store as skip connection
        layers.append(torch.cat(skips5, dim=1))

        return layers[-1], layers[0:-1]


class PoseEncoder(torch.nn.Module):
    """
    Pose network encoder

    Arg(s):
        input_channels : int
            number of channels in input data
        n_filters : list[int]
            number of filters to use for each convolution
        weight_initializer : str
            kaiming_normal, kaiming_uniform, xavier_normal, xavier_uniform
        activation_func : func
            activation function after convolution
        use_batch_norm : bool
            if set, then apply batch normalization
        use_instance_norm : bool
            if set, then apply instance normalization
    """

    def __init__(
        self,
        input_channels=6,
        n_filters=[16, 32, 64, 128, 256, 256, 256],
        weight_initializer="kaiming_uniform",
        activation_func="leaky_relu",
        use_batch_norm=False,
        use_instance_norm=False,
    ):
        super(PoseEncoder, self).__init__()

        activation_func = net_utils.activation_func(activation_func)

        self.conv1 = net_utils.Conv2d(
            input_channels,
            n_filters[0],
            kernel_size=7,
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

        self.conv2 = net_utils.Conv2d(
            n_filters[0],
            n_filters[1],
            kernel_size=5,
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

        self.conv3 = net_utils.Conv2d(
            n_filters[1],
            n_filters[2],
            kernel_size=3,
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

        self.conv4 = net_utils.Conv2d(
            n_filters[2],
            n_filters[3],
            kernel_size=3,
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

        self.conv5 = net_utils.Conv2d(
            n_filters[3],
            n_filters[4],
            kernel_size=3,
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

        self.conv6 = net_utils.Conv2d(
            n_filters[4],
            n_filters[5],
            kernel_size=3,
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

        self.conv7 = net_utils.Conv2d(
            n_filters[5],
            n_filters[6],
            kernel_size=3,
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

    def forward(self, x):
        """
        Forward input x through encoder

        Arg(s):
            x : torch.Tensor[float32]
                input image N x C x H x W
        Returns:
            torch.Tensor[float32] : N x K x h x w output tensor
            None
        """

        layers = [x]

        # Resolution 1/1 -> 1/2
        layers.append(self.conv1(layers[-1]))

        # Resolution 1/2 -> 1/4
        layers.append(self.conv2(layers[-1]))

        # Resolution 1/4 -> 1/8
        layers.append(self.conv3(layers[-1]))

        # Resolution 1/8 -> 1/16
        layers.append(self.conv4(layers[-1]))

        # Resolution 1/16 -> 1/32
        layers.append(self.conv5(layers[-1]))

        # Resolution 1/32 -> 1/64
        layers.append(self.conv6(layers[-1]))

        # Resolution 1/64 -> 1/128
        layers.append(self.conv7(layers[-1]))

        return layers[-1], None


class ResNetEncoder(torch.nn.Module):
    """
    ResNet encoder with skip connections

    Arg(s):
        n_layer : int
            architecture type based on layers: 18, 34, 50
        input_channels : int
            number of channels in input data
        n_filters : list
            number of filters to use for each block
        weight_initializer : str
            kaiming_normal, kaiming_uniform, xavier_normal, xavier_uniform
        activation_func : func
            activation function after convolution
        use_batch_norm : bool
            if set, then apply batch normalization
        use_instance_norm : bool
            if set, then apply instance normalization
        use_depthwise_separable : bool
            if set, then use depthwise separable convolutions instead of convolutions
    """

    def __init__(
        self,
        n_layer,
        input_channels=3,
        n_filters=[32, 64, 128, 256, 256],
        weight_initializer="kaiming_uniform",
        activation_func="leaky_relu",
        use_batch_norm=False,
        use_instance_norm=False,
        use_depthwise_separable=False,
    ):
        super(ResNetEncoder, self).__init__()

        use_bottleneck = False
        if n_layer == 18:
            n_blocks = [2, 2, 2, 2]
            resnet_block = net_utils.ResNetBlock
        elif n_layer == 34:
            n_blocks = [3, 4, 6, 3]
            resnet_block = net_utils.ResNetBlock
        elif n_layer == 50:
            n_blocks = [3, 4, 6, 3]
            use_bottleneck = True
            resnet_block = net_utils.ResNetBottleneckBlock
        else:
            raise ValueError("Only supports 18, 34, 50 layer architecture")

        for n in range(len(n_filters) - len(n_blocks) - 1):
            n_blocks = n_blocks + [n_blocks[-1]]

        assert len(n_filters) == len(n_blocks) + 1

        # Keep track on current block
        block_idx = 0
        filter_idx = 0

        activation_func = net_utils.activation_func(activation_func)

        in_channels, out_channels = [input_channels, n_filters[filter_idx]]

        # Resolution 1/1 -> 1/2
        self.conv1 = net_utils.Conv2d(
            in_channels,
            out_channels,
            kernel_size=7,
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

        # Resolution 1/2 -> 1/4
        self.max_pool = torch.nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        filter_idx = filter_idx + 1

        blocks2 = []
        in_channels, out_channels = [n_filters[filter_idx - 1], n_filters[filter_idx]]
        for n in range(n_blocks[block_idx]):
            if n == 0:
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=1,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                    use_depthwise_separable=False,
                )
            else:
                in_channels = 4 * out_channels if use_bottleneck else out_channels
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=1,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                    use_depthwise_separable=False,
                )

            blocks2.append(block)

        self.blocks2 = torch.nn.Sequential(*blocks2)

        # Resolution 1/4 -> 1/8
        block_idx = block_idx + 1
        filter_idx = filter_idx + 1

        blocks3 = []
        in_channels, out_channels = [n_filters[filter_idx - 1], n_filters[filter_idx]]
        for n in range(n_blocks[block_idx]):
            if n == 0:
                in_channels = 4 * in_channels if use_bottleneck else in_channels
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=2,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                    use_depthwise_separable=False,
                )
            else:
                in_channels = 4 * out_channels if use_bottleneck else out_channels
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=1,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                    use_depthwise_separable=False,
                )

            blocks3.append(block)

        self.blocks3 = torch.nn.Sequential(*blocks3)

        # Resolution 1/8 -> 1/16
        block_idx = block_idx + 1
        filter_idx = filter_idx + 1

        blocks4 = []
        in_channels, out_channels = [n_filters[filter_idx - 1], n_filters[filter_idx]]
        for n in range(n_blocks[block_idx]):
            if n == 0:
                in_channels = 4 * in_channels if use_bottleneck else in_channels
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=2,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                    use_depthwise_separable=use_depthwise_separable,
                )
            else:
                in_channels = 4 * out_channels if use_bottleneck else out_channels
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=1,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                    use_depthwise_separable=use_depthwise_separable,
                )

            blocks4.append(block)

        self.blocks4 = torch.nn.Sequential(*blocks4)

        # Resolution 1/16 -> 1/32
        block_idx = block_idx + 1
        filter_idx = filter_idx + 1

        blocks5 = []
        in_channels, out_channels = [n_filters[filter_idx - 1], n_filters[filter_idx]]
        for n in range(n_blocks[block_idx]):
            if n == 0:
                in_channels = 4 * in_channels if use_bottleneck else in_channels
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=2,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                    use_depthwise_separable=use_depthwise_separable,
                )
            else:
                in_channels = 4 * out_channels if use_bottleneck else out_channels
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=1,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                    use_depthwise_separable=use_depthwise_separable,
                )

            blocks5.append(block)

        self.blocks5 = torch.nn.Sequential(*blocks5)

        # Resolution 1/32 -> 1/64
        block_idx = block_idx + 1
        filter_idx = filter_idx + 1

        if filter_idx < len(n_filters):
            blocks6 = []
            in_channels, out_channels = [
                n_filters[filter_idx - 1],
                n_filters[filter_idx],
            ]
            for n in range(n_blocks[block_idx]):
                if n == 0:
                    in_channels = 4 * in_channels if use_bottleneck else in_channels
                    block = resnet_block(
                        in_channels,
                        out_channels,
                        stride=2,
                        weight_initializer=weight_initializer,
                        activation_func=activation_func,
                        use_batch_norm=use_batch_norm,
                        use_instance_norm=use_instance_norm,
                        use_depthwise_separable=use_depthwise_separable,
                    )
                else:
                    in_channels = 4 * out_channels if use_bottleneck else out_channels
                    block = resnet_block(
                        in_channels,
                        out_channels,
                        stride=1,
                        weight_initializer=weight_initializer,
                        activation_func=activation_func,
                        use_batch_norm=use_batch_norm,
                        use_instance_norm=use_instance_norm,
                        use_depthwise_separable=use_depthwise_separable,
                    )

                blocks6.append(block)

            self.blocks6 = torch.nn.Sequential(*blocks6)
        else:
            self.blocks6 = None

        # Resolution 1/64 -> 1/128
        block_idx = block_idx + 1
        filter_idx = filter_idx + 1

        if filter_idx < len(n_filters):
            blocks7 = []
            in_channels, out_channels = [
                n_filters[filter_idx - 1],
                n_filters[filter_idx],
            ]
            for n in range(n_blocks[block_idx]):
                if n == 0:
                    in_channels = 4 * in_channels if use_bottleneck else in_channels
                    block = resnet_block(
                        in_channels,
                        out_channels,
                        stride=2,
                        weight_initializer=weight_initializer,
                        activation_func=activation_func,
                        use_batch_norm=use_batch_norm,
                        use_instance_norm=use_instance_norm,
                        use_depthwise_separable=use_depthwise_separable,
                    )
                else:
                    in_channels = 4 * out_channels if use_bottleneck else out_channels
                    block = resnet_block(
                        in_channels,
                        out_channels,
                        stride=1,
                        weight_initializer=weight_initializer,
                        activation_func=activation_func,
                        use_batch_norm=use_batch_norm,
                        use_instance_norm=use_instance_norm,
                        use_depthwise_separable=use_depthwise_separable,
                    )

                blocks7.append(block)

            self.blocks7 = torch.nn.Sequential(*blocks7)
        else:
            self.blocks7 = None

    def forward(self, x):
        """
        Forward input x through a ResNet encoder

        Arg(s):
            x : torch.Tensor[float32]
                N x C x H x W input tensor
        Returns:
            torch.Tensor[float32] : N x K x h x w output tensor
            list[torch.Tensor[float32]] : list of skip connections
        """

        layers = [x]

        # Resolution 1/1 -> 1/2
        layers.append(self.conv1(layers[-1]))

        # Resolution 1/2 -> 1/4
        max_pool = self.max_pool(layers[-1])
        layers.append(self.blocks2(max_pool))

        # Resolution 1/4 -> 1/8
        layers.append(self.blocks3(layers[-1]))

        # Resolution 1/8 -> 1/16
        layers.append(self.blocks4(layers[-1]))

        # Resolution 1/16 -> 1/32
        layers.append(self.blocks5(layers[-1]))

        # Resolution 1/32 -> 1/64
        if self.blocks6 is not None:
            layers.append(self.blocks6(layers[-1]))

        # Resolution 1/64 -> 1/128
        if self.blocks7 is not None:
            layers.append(self.blocks7(layers[-1]))

        return layers[-1], layers[1:-1]


class AtrousResNetEncoder(torch.nn.Module):
    """
    ResNet encoder with skip connections

    Arg(s):
        n_layer : int
            architecture type based on layers: 18, 34
        input_channels : int
            number of channels in input data
        n_filters : list
            number of filters to use for each block
        atrous_spatial_pyramid_pool_dilations : list[int]
            list of dilation rates for atrous spatial pyramid pool (ASPP)
        weight_initializer : str
            kaiming_normal, kaiming_uniform, xavier_normal, xavier_uniform
        activation_func : func
            activation function after convolution
        use_batch_norm : bool
            if set, then apply batch normalization
        use_instance_norm : bool
            if set, then apply instance normalization
    """

    def __init__(
        self,
        n_layer,
        input_channels=3,
        n_filters=[32, 64, 128, 256, 256],
        atrous_spatial_pyramid_pool_dilations=None,
        weight_initializer="kaiming_uniform",
        activation_func="leaky_relu",
        use_batch_norm=False,
        use_instance_norm=False,
    ):
        super(AtrousResNetEncoder, self).__init__()

        if n_layer == 18:
            n_blocks = [2, 2, 2, 2]
            resnet_block = net_utils.ResNetBlock
            atrous_resnet_block = net_utils.AtrousResNetBlock
        elif n_layer == 34:
            n_blocks = [3, 4, 6, 3]
            resnet_block = net_utils.ResNetBlock
            atrous_resnet_block = net_utils.AtrousResNetBlock
        else:
            raise ValueError("Only supports 18, 34 layer architecture")

        assert len(n_filters) == len(n_blocks) + 1

        activation_func = net_utils.activation_func(activation_func)
        dilation = 2
        in_channels, out_channels = [input_channels, n_filters[0]]

        # Resolution 1/1 -> 1/2
        self.conv1 = net_utils.Conv2d(
            in_channels,
            out_channels,
            kernel_size=7,
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

        # Resolution 1/2 -> 1/4
        self.max_pool = torch.nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        in_channels, out_channels = [n_filters[0], n_filters[1]]

        blocks2 = []
        for n in range(n_blocks[0]):
            if n == 0:
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=1,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                )
                blocks2.append(block)
            else:
                in_channels = out_channels
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=1,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                )
                blocks2.append(block)
        self.blocks2 = torch.nn.Sequential(*blocks2)

        # Resolution 1/4 -> 1/8
        blocks3 = []
        in_channels, out_channels = [n_filters[1], n_filters[2]]
        for n in range(n_blocks[1]):
            if n == 0:
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=2,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                )
                blocks3.append(block)
            else:
                in_channels = out_channels
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=1,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                )
                blocks3.append(block)
        self.blocks3 = torch.nn.Sequential(*blocks3)

        # Resolution 1/8 with 2x dilation
        blocks4 = []
        in_channels, out_channels = [n_filters[2], n_filters[3]]
        for n in range(n_blocks[2]):
            if n == 0:
                block = atrous_resnet_block(
                    in_channels,
                    out_channels,
                    dilation=dilation,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                )
                dilation = dilation * 2
                blocks4.append(block)
            else:
                in_channels = out_channels
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=1,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                )
                blocks4.append(block)
        self.blocks4 = torch.nn.Sequential(*blocks4)

        # Resolution 1/8 with 4x dilation
        blocks5 = []
        in_channels, out_channels = [n_filters[3], n_filters[4]]
        for n in range(n_blocks[3]):
            if n == 0:
                block = atrous_resnet_block(
                    in_channels,
                    out_channels,
                    dilation=dilation,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                )
                dilation = dilation * 2
                blocks5.append(block)
            else:
                in_channels = out_channels
                block = resnet_block(
                    in_channels,
                    out_channels,
                    stride=1,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                )
                blocks5.append(block)
        self.blocks5 = torch.nn.Sequential(*blocks5)

        if atrous_spatial_pyramid_pool_dilations is not None:
            self.atrous_spatial_pyramid_pool = net_utils.AtrousSpatialPyramidPooling(
                in_channels,
                out_channels,
                dilations=atrous_spatial_pyramid_pool_dilations,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
                use_batch_norm=use_batch_norm,
                use_instance_norm=use_instance_norm,
            )
        else:
            self.atrous_spatial_pyramid_pool = torch.nn.Identity()

    def forward(self, x):
        """
        Forward input x through an atrous ResNet encoder

        Arg(s):
            x : torch.Tensor[float32]
                N x C x H x W input tensor
        Returns:
            torch.Tensor[float32] : N x K x h x w output tensor
            list[torch.Tensor[float32]] : list of skip connections
        """

        layers = [x]

        # Resolution 1/1 -> 1/2
        layers.append(self.conv1(layers[-1]))

        # Resolution 1/2 -> 1/4
        max_pool = self.max_pool(layers[-1])
        layers.append(self.blocks2(max_pool))

        # Resolution 1/4 -> 1/8
        layers.append(self.blocks3(layers[-1]))

        # Resolution 1/8 with 2x dilation
        layers.append(self.blocks4(layers[-1]))

        # Resolution 1/8 with 4x dilation
        # ASPP only used if dilations are given, otherwise pass through (identity)
        block5 = self.blocks5(layers[-1])
        layers.append(self.atrous_spatial_pyramid_pool(block5))

        return layers[-1], layers[1:-1]


class VGGNetEncoder(torch.nn.Module):
    """
    VGGNet encoder with skip connections

    Arg(s):
        input_channels : int
            number of channels in input data
        n_layer : int
            architecture type based on layers: 8, 11, 13
        n_filters : list
            number of filters to use for each block
        weight_initializer : str
            kaiming_normal, kaiming_uniform, xavier_normal, xavier_uniform
        activation_func : func
            activation function after convolution
        use_batch_norm : bool
            if set, then apply batch normalization
        use_instance_norm : bool
            if set, then apply instance normalization
        use_depthwise_separable : bool
            if set, then use depthwise separable convolutions instead of convolutions
    """

    def __init__(
        self,
        n_layer,
        input_channels=3,
        n_filters=[32, 64, 128, 256, 256],
        weight_initializer="kaiming_uniform",
        activation_func="leaky_relu",
        use_batch_norm=False,
        use_instance_norm=False,
        use_depthwise_separable=False,
    ):
        super(VGGNetEncoder, self).__init__()

        if n_layer == 8:
            n_convolutions = [1, 1, 1, 1, 1]
        elif n_layer == 11:
            n_convolutions = [1, 1, 2, 2, 2]
        elif n_layer == 13:
            n_convolutions = [2, 2, 2, 2, 2]
        else:
            raise ValueError("Only supports 8, 11, 13 layer architecture")

        for n in range(len(n_filters) - len(n_convolutions) - 1):
            n_convolutions = n_convolutions + [n_convolutions[-1]]

        # Keep track on current block
        block_idx = 0
        filter_idx = 0

        assert len(n_filters) == len(n_convolutions)

        activation_func = net_utils.activation_func(activation_func)

        # Resolution 1/1 -> 1/2
        stride = 1 if n_convolutions[block_idx] - 1 > 0 else 2
        in_channels, out_channels = [input_channels, n_filters[filter_idx]]

        conv1 = net_utils.Conv2d(
            in_channels,
            out_channels,
            kernel_size=5,
            stride=stride,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

        if n_convolutions[block_idx] - 1 > 0:
            self.conv1 = torch.nn.Sequential(
                conv1,
                net_utils.VGGNetBlock(
                    out_channels,
                    out_channels,
                    n_convolution=n_convolutions[filter_idx] - 1,
                    stride=2,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                    use_depthwise_separable=False,
                ),
            )
        else:
            self.conv1 = conv1

        # Resolution 1/2 -> 1/4
        block_idx = block_idx + 1
        filter_idx = filter_idx + 1
        in_channels, out_channels = [n_filters[filter_idx - 1], n_filters[filter_idx]]

        self.conv2 = net_utils.VGGNetBlock(
            in_channels,
            out_channels,
            n_convolution=n_convolutions[block_idx],
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
            use_depthwise_separable=False,
        )

        # Resolution 1/4 -> 1/8
        block_idx = block_idx + 1
        filter_idx = filter_idx + 1
        in_channels, out_channels = [n_filters[filter_idx - 1], n_filters[filter_idx]]

        self.conv3 = net_utils.VGGNetBlock(
            in_channels,
            out_channels,
            n_convolution=n_convolutions[block_idx],
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
            use_depthwise_separable=False,
        )

        # Resolution 1/8 -> 1/16
        block_idx = block_idx + 1
        filter_idx = filter_idx + 1
        in_channels, out_channels = [n_filters[filter_idx - 1], n_filters[filter_idx]]

        self.conv4 = net_utils.VGGNetBlock(
            in_channels,
            out_channels,
            n_convolution=n_convolutions[block_idx],
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
            use_depthwise_separable=use_depthwise_separable,
        )

        # Resolution 1/16 -> 1/32
        block_idx = block_idx + 1
        filter_idx = filter_idx + 1
        in_channels, out_channels = [n_filters[filter_idx - 1], n_filters[filter_idx]]

        self.conv5 = net_utils.VGGNetBlock(
            in_channels,
            out_channels,
            n_convolution=n_convolutions[block_idx],
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
            use_depthwise_separable=use_depthwise_separable,
        )

        # Resolution 1/32 -> 1/64
        block_idx = block_idx + 1
        filter_idx = filter_idx + 1

        if filter_idx < len(n_filters):
            in_channels, out_channels = [
                n_filters[filter_idx - 1],
                n_filters[filter_idx],
            ]

            self.conv6 = net_utils.VGGNetBlock(
                in_channels,
                out_channels,
                n_convolution=n_convolutions[block_idx],
                stride=2,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
                use_batch_norm=use_batch_norm,
                use_instance_norm=use_instance_norm,
                use_depthwise_separable=use_depthwise_separable,
            )
        else:
            self.conv6 = None

        # Resolution 1/64 -> 1/128
        block_idx = block_idx + 1
        filter_idx = filter_idx + 1

        if filter_idx < len(n_filters):
            in_channels, out_channels = [
                n_filters[filter_idx - 1],
                n_filters[filter_idx],
            ]

            self.conv7 = net_utils.VGGNetBlock(
                in_channels,
                out_channels,
                n_convolution=n_convolutions[block_idx],
                stride=2,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
                use_batch_norm=use_batch_norm,
                use_instance_norm=use_instance_norm,
                use_depthwise_separable=use_depthwise_separable,
            )
        else:
            self.conv7 = None

    def forward(self, x):
        """
        Forward input x through a VGGNet encoder

        Arg(s):
            x : torch.Tensor[float32]
                N x C x H x W input tensor
        Returns:
            torch.Tensor[float32] : N x K x h x w output tensor
        """

        layers = [x]

        # Resolution 1/1 -> 1/2
        layers.append(self.conv1(layers[-1]))

        # Resolution 1/2 -> 1/4
        layers.append(self.conv2(layers[-1]))

        # Resolution 1/4 -> 1/8
        layers.append(self.conv3(layers[-1]))

        # Resolution 1/8 -> 1/32
        layers.append(self.conv4(layers[-1]))

        # Resolution 1/16 -> 1/32
        layers.append(self.conv5(layers[-1]))

        # Resolution 1/32 -> 1/64
        if self.conv6 is not None:
            layers.append(self.conv6(layers[-1]))

        # Resolution 1/64 -> 1/128
        if self.conv7 is not None:
            layers.append(self.conv7(layers[-1]))

        return layers[-1], layers[1:-1]


class AtrousVGGNetEncoder(torch.nn.Module):
    """
    Atrous VGGNet encoder with skip connections

    Arg(s):
        input_channels : int
            number of channels in input data
        n_layer : int
            architecture type based on layers: 8, 11, 13
        n_filters : list
            number of filters to use for each block
        weight_initializer : str
            kaiming_normal, kaiming_uniform, xavier_normal, xavier_uniform
        activation_func : func
            activation function after convolution
        use_batch_norm : bool
            if set, then apply batch normalization
        use_instance_norm : bool
            if set, then apply instance normalization
    """

    def __init__(
        self,
        n_layer,
        input_channels=3,
        n_filters=[32, 64, 128, 256, 256],
        weight_initializer="kaiming_uniform",
        activation_func="leaky_relu",
        use_batch_norm=False,
        use_instance_norm=False,
    ):
        super(AtrousVGGNetEncoder, self).__init__()

        if n_layer == 8:
            n_convolutions = [1, 1, 1, 1, 1]
        elif n_layer == 11:
            n_convolutions = [1, 1, 2, 2, 2]
        elif n_layer == 13:
            n_convolutions = [2, 2, 2, 2, 2]
        else:
            raise ValueError("Only supports 8, 11, 13 layer architecture")

        assert len(n_filters) == len(n_convolutions)

        activation_func = net_utils.activation_func(activation_func)
        dilation = 2

        # Resolution 1/1 -> 1/2
        stride = 1 if n_convolutions[0] - 1 > 0 else 2
        in_channels, out_channels = [input_channels, n_filters[0]]

        conv1 = net_utils.Conv2d(
            in_channels,
            out_channels,
            kernel_size=5,
            stride=stride,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

        if n_convolutions[0] - 1 > 0:
            self.conv1 = torch.nn.Sequential(
                conv1,
                net_utils.VGGNetBlock(
                    out_channels,
                    out_channels,
                    n_convolution=n_convolutions[0] - 1,
                    stride=2,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                ),
            )
        else:
            self.conv1 = conv1

        # Resolution 1/2 -> 1/4
        in_channels, out_channels = [n_filters[0], n_filters[1]]
        self.conv2 = net_utils.VGGNetBlock(
            in_channels,
            out_channels,
            n_convolution=n_convolutions[1],
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

        # Resolution 1/4 -> 1/8
        in_channels, out_channels = [n_filters[1], n_filters[2]]
        self.conv3 = net_utils.VGGNetBlock(
            in_channels,
            out_channels,
            n_convolution=n_convolutions[2],
            stride=2,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

        # Resolution 1/8 with 2x dilation
        in_channels, out_channels = [n_filters[2], n_filters[3]]
        self.conv4 = net_utils.AtrousVGGNetBlock(
            in_channels,
            out_channels,
            n_convolution=n_convolutions[3],
            dilation=dilation,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

        # Resolution 1/8 with 4x dilation
        in_channels, out_channels = [n_filters[3], n_filters[4]]
        self.conv5 = net_utils.AtrousVGGNetBlock(
            in_channels,
            out_channels,
            n_convolution=n_convolutions[4],
            dilation=dilation,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
        )

    def forward(self, x):
        """
        Forward input x through an atrous VGGNet encoder

        Arg(s):
            x : torch.Tensor[float32]
                N x C x H x W input tensor
        Returns:
            torch.Tensor[float32] : N x K x h x w output tensor
        """

        layers = [x]

        # Resolution 1/1 -> 1/2
        layers.append(self.conv1(layers[-1]))

        # Resolution 1/2 -> 1/4
        layers.append(self.conv2(layers[-1]))

        # Resolution 1/4 -> 1/8
        layers.append(self.conv3(layers[-1]))

        # Resolution 1/8 with 2x dilation
        layers.append(self.conv4(layers[-1]))

        # Resolution 1/8 with 4x dilation
        layers.append(self.conv5(layers[-1]))

        return layers[-1], layers[1:-1]


"""
Decoder architectures
"""


class MultiScaleDecoder(torch.nn.Module):
    """
    Multi-scale decoder with skip connections

    Arg(s):
        input_channels : int
            number of channels in input latent vector
        output_channels : int
            number of channels or classes in output
        n_resolution : int
            number of output resolutions (scales) for multi-scale prediction
        n_filters : list[int]
            number of filters to use at each decoder block
        n_skips : list[int]
            number of filters from skip connections
        weight_initializer : str
            kaiming_normal, kaiming_uniform, xavier_normal, xavier_uniform
        activation_func : func
            activation function after convolution
        output_func : func
            activation function for output
        use_batch_norm : bool
            if set, then apply batch normalization
        use_instance_norm : bool
            if set, then apply instance normalization
        deconv_type : str
            deconvolution types available: transpose, up
    """

    def __init__(
        self,
        input_channels=256,
        output_channels=1,
        n_resolution=4,
        n_filters=[256, 128, 64, 32, 16],
        n_skips=[256, 128, 64, 32, 0],
        weight_initializer="kaiming_uniform",
        activation_func="leaky_relu",
        output_func="linear",
        use_batch_norm=False,
        use_instance_norm=False,
        deconv_type="transpose",
    ):
        super(MultiScaleDecoder, self).__init__()

        network_depth = len(n_filters)

        assert network_depth < 8, "Does not support network depth of 8 or more"
        assert n_resolution > 0 and n_resolution < network_depth

        self.n_resolution = n_resolution
        self.output_func = output_func

        activation_func = net_utils.activation_func(activation_func)
        output_func = net_utils.activation_func(output_func)

        # Upsampling from lower to full resolution requires multi-scale
        if "upsample" in self.output_func and self.n_resolution < 2:
            self.n_resolution = 2

        filter_idx = 0

        in_channels, skip_channels, out_channels = [
            input_channels,
            n_skips[filter_idx],
            n_filters[filter_idx],
        ]

        # Resolution 1/128 -> 1/64
        if network_depth > 6:
            self.deconv6 = net_utils.DecoderBlock(
                in_channels,
                skip_channels,
                out_channels,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
                use_batch_norm=use_batch_norm,
                use_instance_norm=use_instance_norm,
                deconv_type=deconv_type,
            )

            filter_idx = filter_idx + 1

            in_channels, skip_channels, out_channels = [
                n_filters[filter_idx - 1],
                n_skips[filter_idx],
                n_filters[filter_idx],
            ]
        else:
            self.deconv6 = None

        # Resolution 1/64 -> 1/32
        if network_depth > 5:
            self.deconv5 = net_utils.DecoderBlock(
                in_channels,
                skip_channels,
                out_channels,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
                use_batch_norm=use_batch_norm,
                use_instance_norm=use_instance_norm,
                deconv_type=deconv_type,
            )

            filter_idx = filter_idx + 1

            in_channels, skip_channels, out_channels = [
                n_filters[filter_idx - 1],
                n_skips[filter_idx],
                n_filters[filter_idx],
            ]
        else:
            self.deconv5 = None

        # Resolution 1/32 -> 1/16
        if network_depth > 4:
            self.deconv4 = net_utils.DecoderBlock(
                in_channels,
                skip_channels,
                out_channels,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
                use_batch_norm=use_batch_norm,
                use_instance_norm=use_instance_norm,
                deconv_type=deconv_type,
            )

            filter_idx = filter_idx + 1

            in_channels, skip_channels, out_channels = [
                n_filters[filter_idx - 1],
                n_skips[filter_idx],
                n_filters[filter_idx],
            ]
        else:
            self.deconv4 = None

        # Resolution 1/16 -> 1/8
        if network_depth > 3:
            self.deconv3 = net_utils.DecoderBlock(
                in_channels,
                skip_channels,
                out_channels,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
                use_batch_norm=use_batch_norm,
                use_instance_norm=use_instance_norm,
                deconv_type=deconv_type,
            )

            if self.n_resolution > 3:
                self.output3 = net_utils.Conv2d(
                    out_channels,
                    output_channels,
                    kernel_size=3,
                    stride=1,
                    weight_initializer=weight_initializer,
                    activation_func=None,
                    use_batch_norm=False,
                    use_instance_norm=False,
                )
            else:
                self.output3 = None

            # Resolution 1/8 -> 1/4
            filter_idx = filter_idx + 1

            in_channels, skip_channels, out_channels = [
                n_filters[filter_idx - 1],
                n_skips[filter_idx],
                n_filters[filter_idx],
            ]

            if self.n_resolution > 3:
                skip_channels = skip_channels + output_channels
        else:
            self.deconv3 = None

        if network_depth > 2:
            self.deconv2 = net_utils.DecoderBlock(
                in_channels,
                skip_channels,
                out_channels,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
                use_batch_norm=use_batch_norm,
                use_instance_norm=use_instance_norm,
                deconv_type=deconv_type,
            )

            if self.n_resolution > 2:
                self.output2 = net_utils.Conv2d(
                    out_channels,
                    output_channels,
                    kernel_size=3,
                    stride=1,
                    weight_initializer=weight_initializer,
                    activation_func=output_func,
                    use_batch_norm=False,
                    use_instance_norm=False,
                )
            else:
                self.output2 = None

            # Resolution 1/4 -> 1/2
            filter_idx = filter_idx + 1

            in_channels, skip_channels, out_channels = [
                n_filters[filter_idx - 1],
                n_skips[filter_idx],
                n_filters[filter_idx],
            ]

            if self.n_resolution > 2:
                skip_channels = skip_channels + output_channels
        else:
            self.deconv2 = None

        self.deconv1 = net_utils.DecoderBlock(
            in_channels,
            skip_channels,
            out_channels,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
            deconv_type=deconv_type,
        )

        if self.n_resolution > 1:
            self.output1 = net_utils.Conv2d(
                out_channels,
                output_channels,
                kernel_size=3,
                stride=1,
                weight_initializer=weight_initializer,
                activation_func=output_func,
                use_batch_norm=False,
                use_instance_norm=False,
            )
        else:
            self.output1 = None

        # Resolution 1/2 -> 1/1
        filter_idx = filter_idx + 1

        in_channels, skip_channels, out_channels = [
            n_filters[filter_idx - 1],
            n_skips[filter_idx],
            n_filters[filter_idx],
        ]

        if self.n_resolution > 1:
            skip_channels = skip_channels + output_channels

        self.deconv0 = net_utils.DecoderBlock(
            in_channels,
            skip_channels,
            out_channels,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=use_batch_norm,
            use_instance_norm=use_instance_norm,
            deconv_type=deconv_type,
        )

        self.output0 = net_utils.Conv2d(
            out_channels,
            output_channels,
            kernel_size=3,
            stride=1,
            weight_initializer=weight_initializer,
            activation_func=output_func,
            use_batch_norm=False,
            use_instance_norm=False,
        )

    def forward(self, x, skips, shape=None):
        """
        Forward latent vector x through decoder network

        Arg(s):
            x : torch.Tensor[float32]
                latent vector
            skips : list[torch.Tensor[float32]]
                list of skip connection tensors (earlier are larger resolution)
            shape : tuple[int]
                (height, width) tuple denoting output size
        Returns:
            list[torch.Tensor[float32]] : list of outputs at multiple scales
        """

        layers = [x]
        outputs = []

        # Start at the end and walk backwards through skip connections
        n = len(skips) - 1

        # Resolution 1/128 -> 1/64
        if self.deconv6 is not None:
            layers.append(self.deconv6(layers[-1], skips[n]))
            n = n - 1

        # Resolution 1/64 -> 1/32
        if self.deconv5 is not None:
            layers.append(self.deconv5(layers[-1], skips[n]))
            n = n - 1

        # Resolution 1/32 -> 1/16
        if self.deconv4 is not None:
            layers.append(self.deconv4(layers[-1], skips[n]))
            n = n - 1

        # Resolution 1/16 -> 1/8
        if self.deconv3 is not None:
            layers.append(self.deconv3(layers[-1], skips[n]))

            if self.n_resolution > 3:
                output3 = self.output3(layers[-1])
                outputs.append(output3)

                if n > 0:
                    upsample_output3 = torch.nn.functional.interpolate(
                        input=outputs[-1],
                        size=skips[n - 1].shape[-2:],
                        mode="bilinear",
                        align_corners=True,
                    )
                else:
                    upsample_output3 = torch.nn.functional.interpolate(
                        input=outputs[-1],
                        scale_factor=2,
                        mode="bilinear",
                        align_corners=True,
                    )

            n = n - 1

        # Resolution 1/8 -> 1/4
        if self.deconv2 is not None:
            if skips[n] is not None:
                skip = (
                    torch.cat([skips[n], upsample_output3], dim=1)
                    if self.n_resolution > 3
                    else skips[n]
                )
            else:
                skip = skips[n]
            layers.append(self.deconv2(layers[-1], skip))

            if self.n_resolution > 2:
                output2 = self.output2(layers[-1])
                outputs.append(output2)

                if n > 0:
                    upsample_output2 = torch.nn.functional.interpolate(
                        input=outputs[-1],
                        size=skips[n - 1].shape[-2:],
                        mode="bilinear",
                        align_corners=True,
                    )
                else:
                    upsample_output2 = torch.nn.functional.interpolate(
                        input=outputs[-1],
                        scale_factor=2,
                        mode="bilinear",
                        align_corners=True,
                    )

            n = n - 1

        # Resolution 1/4 -> 1/2
        if skips[n] is not None:
            skip = (
                torch.cat([skips[n], upsample_output2], dim=1)
                if self.n_resolution > 2
                else skips[n]
            )
        else:
            skip = skips[n]
        layers.append(self.deconv1(layers[-1], skip))

        if self.n_resolution > 1:
            output1 = self.output1(layers[-1])
            outputs.append(output1)

            if n > 0:
                upsample_output1 = torch.nn.functional.interpolate(
                    input=outputs[-1],
                    size=skips[n - 1].shape[-2:],
                    mode="bilinear",
                    align_corners=True,
                )
            else:
                upsample_output1 = torch.nn.functional.interpolate(
                    input=outputs[-1],
                    scale_factor=2,
                    mode="bilinear",
                    align_corners=True,
                )

        # Resolution 1/2 -> 1/1
        n = n - 1

        if "upsample" in self.output_func:
            output0 = upsample_output1
        else:
            if self.n_resolution > 1:
                # If there is skip connection at layer 0
                if skips[n] is not None and n == 0:
                    skip = (
                        torch.cat([skips[n], upsample_output1], dim=1)
                        if n == 0
                        else upsample_output1
                    )
                else:
                    skip = upsample_output1
                layers.append(self.deconv0(layers[-1], skip))
            else:
                if skips[n] is not None and n == 0:
                    layers.append(self.deconv0(layers[-1], skips[n]))
                else:
                    layers.append(self.deconv0(layers[-1], shape=shape[-2:]))

            output0 = self.output0(layers[-1])

        outputs.append(output0)

        return outputs


class PoseDecoder(torch.nn.Module):
    """
    Pose Decoder 6 DOF

    Arg(s):
        rotation_parameterization : str
            axis
        input_channels : int
            number of channels in input latent vector
        n_filters : int list
            number of filters to use at each decoder block
        weight_initializer : str
            kaiming_normal, kaiming_uniform, xavier_normal, xavier_uniform
        activation_func : func
            activation function after convolution
        use_batch_norm : bool
            if set, then apply batch normalization
        use_instance_norm : bool
            if set, then apply instance normalization
    """

    def __init__(
        self,
        rotation_parameterization,
        input_channels=256,
        n_filters=[],
        weight_initializer="kaiming_uniform",
        activation_func="leaky_relu",
        use_batch_norm=False,
        use_instance_norm=False,
    ):
        super(PoseDecoder, self).__init__()

        self.rotation_parameterization = rotation_parameterization

        activation_func = net_utils.activation_func(activation_func)

        if len(n_filters) > 0:
            layers = []
            in_channels = input_channels

            for out_channels in n_filters:
                conv = net_utils.Conv2d(
                    in_channels=in_channels,
                    out_channels=out_channels,
                    kernel_size=3,
                    stride=2,
                    weight_initializer=weight_initializer,
                    activation_func=activation_func,
                    use_batch_norm=use_batch_norm,
                    use_instance_norm=use_instance_norm,
                )
                layers.append(conv)
                in_channels = out_channels

            conv = net_utils.Conv2d(
                in_channels=in_channels,
                out_channels=6,
                kernel_size=1,
                stride=1,
                weight_initializer=weight_initializer,
                activation_func=None,
                use_batch_norm=False,
                use_instance_norm=False,
            )
            layers.append(conv)

            self.conv = torch.nn.Sequential(*layers)
        else:
            self.conv = net_utils.Conv2d(
                in_channels=input_channels,
                out_channels=6,
                kernel_size=1,
                stride=1,
                weight_initializer=weight_initializer,
                activation_func=None,
                use_batch_norm=False,
                use_instance_norm=False,
            )

    def forward(self, x):
        conv_output = self.conv(x)
        pose_mean = torch.mean(conv_output, [2, 3])
        dof = 0.01 * pose_mean
        posemat = net_utils.pose_matrix(
            dof, rotation_parameterization=self.rotation_parameterization
        )

        return posemat


class SparseToDensePool(torch.nn.Module):
    """
    Converts sparse inputs to dense outputs using max and min pooling
    with different kernel sizes and combines them with 1 x 1 convolutions

    Arg(s):
        input_channels : int
            number of channels to be fed to max and/or average pool(s)
        min_pool_sizes : list[int]
            list of min pool sizes s (kernel size is s x s)
        max_pool_sizes : list[int]
            list of max pool sizes s (kernel size is s x s)
        n_filter : int
            number of filters for 1 x 1 convolutions
        n_convolution : int
            number of 1 x 1 convolutions to use for balancing detail and density
        weight_initializer : str
            kaiming_normal, kaiming_uniform, xavier_normal, xavier_uniform
        activation_func : func
            activation function after convolution
    """

    def __init__(
        self,
        input_channels,
        min_pool_sizes=[3, 5, 7, 9],
        max_pool_sizes=[3, 5, 7, 9],
        n_filter=8,
        n_convolution=3,
        weight_initializer="kaiming_uniform",
        activation_func="leaky_relu",
    ):
        super(SparseToDensePool, self).__init__()

        activation_func = net_utils.activation_func(activation_func)

        self.min_pool_sizes = [s for s in min_pool_sizes if s > 1]

        self.max_pool_sizes = [s for s in max_pool_sizes if s > 1]

        # Construct min pools
        self.min_pools = []
        for s in self.min_pool_sizes:
            padding = s // 2
            pool = torch.nn.MaxPool2d(kernel_size=s, stride=1, padding=padding)
            self.min_pools.append(pool)

        # Construct max pools
        self.max_pools = []
        for s in self.max_pool_sizes:
            padding = s // 2
            pool = torch.nn.MaxPool2d(kernel_size=s, stride=1, padding=padding)
            self.max_pools.append(pool)

        self.len_pool_sizes = len(self.min_pool_sizes) + len(self.max_pool_sizes)

        in_channels = len(self.min_pool_sizes) + len(self.max_pool_sizes)

        pool_convs = []
        for n in range(n_convolution):
            conv = net_utils.Conv2d(
                in_channels,
                n_filter,
                kernel_size=1,
                stride=1,
                weight_initializer=weight_initializer,
                activation_func=activation_func,
                use_batch_norm=False,
                use_instance_norm=False,
            )
            pool_convs.append(conv)

            # Set new input channels as output channels
            in_channels = n_filter

        self.pool_convs = torch.nn.Sequential(*pool_convs)

        in_channels = n_filter + input_channels

        self.conv = net_utils.Conv2d(
            in_channels,
            n_filter,
            kernel_size=3,
            stride=1,
            weight_initializer=weight_initializer,
            activation_func=activation_func,
            use_batch_norm=False,
            use_instance_norm=False,
        )

    def forward(self, x):
        # Input depth
        z = torch.unsqueeze(x[:, 0, ...], dim=1)

        pool_pyramid = []

        # Use min and max pooling to densify and increase receptive field
        for pool, s in zip(self.min_pools, self.min_pool_sizes):
            # Set flag (999) for any zeros and max pool on -z then revert the values
            z_pool = -pool(torch.where(z == 0, -999 * torch.ones_like(z), -z))
            # Remove any 999 from the results
            z_pool = torch.where(z_pool == 999, torch.zeros_like(z), z_pool)

            pool_pyramid.append(z_pool)

        for pool, s in zip(self.max_pools, self.max_pool_sizes):
            z_pool = pool(z)

            pool_pyramid.append(z_pool)

        # Stack max and minpools into pyramid
        pool_pyramid = torch.cat(pool_pyramid, dim=1)

        # Learn weights for different kernel sizes, and near and far structures
        pool_convs = self.pool_convs(pool_pyramid)

        pool_convs = torch.cat([pool_convs, x], dim=1)

        return self.conv(pool_convs)
