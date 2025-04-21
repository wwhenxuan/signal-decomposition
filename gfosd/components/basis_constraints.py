"""
Basis Class

This encodes the constraint that the component is representable in basis form,
i.e

    x = Az,

where A is some basis matrix. This also includes any additional penalty on z
that is avaible in the menu of g functions.

"""

import numpy as np
import scipy.sparse as sp
from gfosd.components.base_graph_class import GraphComponent
from gfosd.components.utilities import make_basis_matrix, make_regularization_matrix


class Basis(GraphComponent):
    def __init__(self, basis, penalty=None, *args, **kwargs):
        self._basis = basis
        # penalty can be None, an atom name (e.g. 'sum_square' or 'abs'), or PSD matrix (2D numpy array)
        self._penalty = penalty
        if isinstance(penalty, np.ndarray) or isinstance(penalty, sp.spmatrix):
            self._penalty = "matrix"
            self._pmat = penalty
        else:
            self._ndim = None
        super().__init__(*args, **kwargs)
        self._has_helpers = True

    def _set_z_size(self):
        self._z_size = self._basis.shape[1]

    def _make_B(self):
        basis_len = self._basis.shape[0]
        # below allows for lazy evaluation of the full basis dictionary,
        # allowing for the user to define a basis based on a known shorter
        # period without knowing the signal length ahead of time
        if basis_len != self._T:
            num_periods = int(np.ceil(self._T / basis_len))
            M = sp.vstack([self._basis] * num_periods)
            M = M.tocsr()
            M = M[: self._T]
            self._basis = M
        self._B = self._basis * -1

    def _make_g(self, size):
        if (
            (self._penalty is None)
            or (self._penalty == "sum_square")
            or (self._penalty == "matrix")
        ):
            g = []
        else:
            # typically 'abs', 'huber', or 'quantile'
            g = [
                {
                    "g": self._penalty,
                    "args": {"weight": self.weight},
                    "range": (0, size),
                }
            ]
        return g

    def _make_P(self, size):
        if self._penalty == "matrix":
            P = sp.dia_matrix(self._pmat)
            P = P.power(2)
        elif np.all(self._penalty == "sum_square"):
            P = self.weight * sp.eye(size)
        else:
            P = sp.dok_matrix(2 * (size,))
        return P


class Periodic(Basis):
    def __init__(self, period, *args, **kwargs):
        self._period = period
        M = sp.eye(period)
        super().__init__(M, *args, **kwargs)


class Fourier(Basis):
    def __init__(
        self,
        num_harmonics,
        length,
        periods,
        standing_wave=False,
        trend=False,
        max_cross_k=None,
        custom_basis=None,
        weight=1,
        **kwargs,
    ):
        _B = make_basis_matrix(
            num_harmonics,
            length,
            periods,
            standing_wave,
            trend,
            max_cross_k,
            custom_basis,
        )
        _D = make_regularization_matrix(
            num_harmonics,
            weight,
            periods,
            standing_wave,
            trend,
            max_cross_k,
            custom_basis,
        )
        super().__init__(basis=_B, penalty=_D, weight=weight, **kwargs)
