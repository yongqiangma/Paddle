# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import paddle.fluid as fluid
import paddle.complex as cpx
import paddle.fluid.dygraph as dg
import numpy as np
import unittest


class TestComplexReshape(unittest.TestCase):
    def test_case1(self):
        x_np = np.random.randn(2, 3, 4) + 1j * np.random.randn(2, 3, 4)
        shape = (2, -1)

        place = fluid.CPUPlace()
        with dg.guard(place):
            x_var = dg.to_variable(x_np)
            y_var = cpx.reshape(x_var, shape)
            y_np = y_var.numpy()

        np.testing.assert_allclose(np.reshape(x_np, shape), y_np)

    def test_case2(self):
        x_np = np.random.randn(2, 3, 4) + 1j * np.random.randn(2, 3, 4)
        shape = (0, -1)
        shape_ = (2, 12)

        place = fluid.CUDAPlace(0) if fluid.is_compiled_with_cuda(
        ) else fluid.CPUPlace()
        with dg.guard(place):
            x_var = dg.to_variable(x_np)
            y_var = cpx.reshape(x_var, shape, inplace=True)
            y_np = y_var.numpy()

        np.testing.assert_allclose(np.reshape(x_np, shape_), y_np)


if __name__ == "__main__":
    unittest.main()
