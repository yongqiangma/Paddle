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

from __future__ import print_function

import unittest, os
import numpy as np
from paddle.fluid.tests.unittests.op_test import OpTest, skip_check_grad_ci


@skip_check_grad_ci(reason="DNNL's MatMul doesn't implemend grad kernel.")
class TestDnnlMatMulOp(OpTest):
    def generate_data(self):
        self.x = np.random.random((25, 2, 2)).astype("float32")
        self.y = np.random.random((25, 2, 2)).astype("float32")
        self.alpha = 1.0
        self.out = self.alpha * np.matmul(self.x, self.y)

    def set_attributes(self):
        self.alpha = self.alpha if hasattr(self, 'alpha') else 1.0
        self.attrs = {'alpha': self.alpha}

    def setUp(self):
        # Set max isa, otherwise fails on SKX and earlier
        os.environ["DNNL_MAX_CPU_ISA"] = "AVX"
        self.op_type = "matmul"
        self._cpu_only = True
        self.use_mkldnn = True
        self.generate_data()
        self.set_attributes()
        self.attrs['use_mkldnn'] = True

        self.inputs = {'X': self.x, 'Y': self.y}
        self.outputs = {'Out': self.out}

    def test_check_output(self):
        self.check_output()


class TestDnnlMatMulOpAlpha(TestDnnlMatMulOp):
    def generate_data(self):
        self.x = np.random.random((17, 2, 3)).astype("float32")
        self.y = np.random.random((17, 3, 2)).astype("float32")
        self.alpha = 2.0
        self.out = self.alpha * np.matmul(self.x, self.y)


class TestDnnlMatMulOp2D(TestDnnlMatMulOp):
    def print_tensor(self, name, tensor):
        print(name)
        print(tensor)

    def generate_data(self):
        self.x = np.random.random((12, 9)).astype("float32")
        self.y = np.random.random((9, 12)).astype("float32")
        self.out = np.matmul(self.x, self.y)


class TestDnnlMatMulOpTransposeX(TestDnnlMatMulOp):
    def generate_data(self):
        self.x = np.random.random((12, 9)).astype("float32")
        self.y = np.random.random((12, 9)).astype("float32")
        self.out = np.matmul(np.transpose(self.x), self.y)

    def set_attributes(self):
        self.attrs = {'transpose_X': True}


class TestDnnlMatMulOpTransposeY(TestDnnlMatMulOp):
    def generate_data(self):
        self.x = np.random.random((12, 9)).astype("float32")
        self.y = np.random.random((12, 9)).astype("float32")
        self.out = np.matmul(self.x, np.transpose(self.y))

    def set_attributes(self):
        self.attrs = {'transpose_Y': True}


class TestDnnlMatMulOpTransposeY3D(TestDnnlMatMulOp):
    def generate_data(self):
        self.x = np.random.random((17, 3, 2)).astype("float32")
        self.y = np.random.random((17, 3, 2)).astype("float32")
        self.out = np.matmul(self.x, np.transpose(self.y, (0, 2, 1)))

    def set_attributes(self):
        self.attrs = {'transpose_Y': True}


class TestDnnlMatMulOpInt8NoScales(TestDnnlMatMulOp):
    def generate_data(self):
        self.x = np.random.random((12, 9)).astype("int8")
        self.y = np.random.random((9, 12)).astype("int8")
        self.out = np.matmul(self.x, self.y)


class TestDnnlMatMulOpInt8(TestDnnlMatMulOp):
    def quantize(self, tensor):
        scale = 127. / np.abs(np.amax(tensor))
        quantized = np.round(scale * tensor).astype("int8")
        return scale, quantized

    def generate_data(self):
        x_float = np.random.random((12, 9)).astype("float32")
        self.x_scale, self.x = self.quantize(x_float)

        y_float = np.random.random((9, 12)).astype("float32")
        self.y_scale, self.y = self.quantize(y_float)

        out_float = np.matmul(x_float, y_float)
        self.out_scale, self.out = self.quantize(out_float)

    def set_attributes(self):
        self.attrs = {
            'Scale_x': self.x_scale,
            'Scale_y': self.y_scale,
            'Scale_out': self.out_scale,
        }

    def test_check_output(self):
        int_atol = 1
        self.check_output(atol=int_atol)


class TestDnnlMatMulOpInt8ForceFP32(TestDnnlMatMulOpInt8):
    def generate_data(self):
        x_float = np.random.random((12, 9)).astype("float32")
        self.x_scale, self.x = self.quantize(x_float)

        y_float = np.random.random((9, 12)).astype("float32")
        self.y_scale, self.y = self.quantize(y_float)

        out_float = np.matmul(x_float, y_float)
        self.out = out_float

    def set_attributes(self):
        self.attrs = {
            'Scale_x': self.x_scale,
            'Scale_y': self.y_scale,
            'force_fp32_output': True
        }


class TestDnnlMatMulOpInt8ForceFP32BasicScales(TestDnnlMatMulOp):
    def generate_data(self):
        self.x = np.random.randint(0, 3, (12, 9)).astype("int8")
        self.y = np.random.randint(0, 3, (9, 12)).astype("int8")
        self.out = np.matmul(self.x, self.y).astype("float32")

    def set_attributes(self):
        self.attrs = {'force_fp32_output': True}


@skip_check_grad_ci(reason="Tests inference only optimization.")
class TestMatMulOpTransposeReshapeEmptyFloat(OpTest):
    def init_data_type(self):
        self.data_type_ = np.float32

    def generate_data(self):
        self.bs = 1
        self.x = np.random.random([self.bs, 128, 128]).astype(self.data_type_)
        self.y = np.random.random([self.bs, 128, 64]).astype(self.data_type_)

    def init_params_and_out(self):
        self.transpose_out = []
        self.reshape_out = []
        self.out = np.matmul(self.x, self.y)

    def setUp(self):
        os.environ["DNNL_MAX_CPU_ISA"] = "AVX"
        self.op_type = "matmul"
        self._cpu_only = True
        self.use_mkldnn = True
        self.init_data_type()
        self.generate_data()
        self.init_params_and_out()

        self.inputs = {'X': self.x, 'Y': self.y}
        self.attrs = {'use_mkldnn': self.use_mkldnn}

        if len(self.reshape_out) > 0:
            self.attrs['fused_reshape_Out'] = self.reshape_out
        if len(self.transpose_out) > 0:
            self.attrs['fused_transpose_Out'] = self.transpose_out

        self.inputs = {'X': self.x, 'Y': self.y}
        self.outputs = {'Out': self.out}

    def test_check_output(self):
        self.check_output()

    def check_raise_error(self, msg):
        try:
            self.check_output()
        except Exception as e:
            if msg in str(e):
                raise AttributeError
            else:
                print(e)


class TestMatMulOpTransposeReshapeIntEmptyInt(
        TestMatMulOpTransposeReshapeEmptyFloat):
    def init_data_type(self):
        self.data_type_ = np.int8


class TestMatMulOpTransposeReshapeBasicFloat(
        TestMatMulOpTransposeReshapeEmptyFloat):
    def generate_data(self):
        self.bs = 8
        self.x = np.random.random(
            [self.bs, 12, 128, 128]).astype(self.data_type_)
        self.y = np.random.random(
            [self.bs, 12, 128, 64]).astype(self.data_type_)

    def init_params_and_out(self):
        self.transpose_out = [0, 2, 1, 3]
        self.reshape_out = [0, 0, self.x.shape[1] * self.y.shape[-1]]
        self.out = np.matmul(self.x, self.y).transpose([0, 2, 1, 3]).reshape(
            [self.bs, -1, self.x.shape[1] * self.y.shape[-1]])


class TestMatMulOpTransposeReshapeBasicInt(
        TestMatMulOpTransposeReshapeBasicFloat):
    def init_data_type(self):
        self.data_type_ = np.int8


class TestMatMulOpTransposeReshapeOtherDimFloat(
        TestMatMulOpTransposeReshapeBasicFloat):
    def generate_data(self):
        self.bs = 11
        self.x = np.random.random([self.bs, 12, 14, 18]).astype(self.data_type_)
        self.y = np.random.random([self.bs, 12, 18, 13]).astype(self.data_type_)


class TestMatMulOpTransposeReshapeOtherDimInt(
        TestMatMulOpTransposeReshapeOtherDimFloat):
    def init_data_type(self):
        self.data_type_ = np.int8


class TestMatMulOpTransposeReshapeTransposeAxisNotSupportedException(
        TestMatMulOpTransposeReshapeBasicFloat):
    def init_params_and_out(self):
        self.transpose_out = [0, 1, 2, 3]
        self.reshape_out = [0, 0, self.x.shape[1] * self.y.shape[-1]]
        self.out = np.matmul(self.x, self.y)

    def test_check_output(self):
        self.assertRaises(AttributeError, self.check_raise_error,
                          'InvalidArgumentError: supported transpose axis '
                          'for the fuse are {0, 2, 1, 3}')


class TestMatMulOpTransposeReshapeTransposeRankNotSupportedException(
        TestMatMulOpTransposeReshapeBasicFloat):
    def init_params_and_out(self):
        self.transpose_out = [0, 2, 1]
        self.reshape_out = [0, 0, self.x.shape[1] * self.y.shape[-1]]
        self.out = np.matmul(self.x, self.y)

    def test_check_output(self):
        self.assertRaises(
            AttributeError, self.check_raise_error,
            'InvalidArgumentError: transpose_out supported rank is 4')


class TestMatMulOpTransposeReshapeRankOfReshapeNotSupportedException(
        TestMatMulOpTransposeReshapeBasicFloat):
    def init_params_and_out(self):
        self.transpose_out = [0, 2, 1, 3]
        self.reshape_out = [0, 0]
        self.out = np.matmul(self.x, self.y)

    def test_check_output(self):
        self.assertRaises(
            AttributeError, self.check_raise_error,
            'InvalidArgumentError: reshape_out supported rank is 3')


if __name__ == "__main__":
    unittest.main()
