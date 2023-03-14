import math


class BivariateCumulativeStudentDistribution:
    """
    Cumulative Student t-distribution
    Implemented following the formulas from Dunnett, C.W. and
    Sobel, M. (1954). A bivariate generalization of Student
    t-distribution with tables for certain special
    cases. Biometrika 41, 153–169.
    """
    epsilon = 1.0e-8

    def __init__(self, n: int, rho):
        self._n = n
        self._rho = rho

    def __call__(self, x, y):
        return self.p_n(x, y, self._n, self._rho)

    @staticmethod
    def p_n(h, k, n: int, rho):
        """ this calculates the cdf """
        un_cor = 1.0 - rho * rho

        div = 4 * math.sqrt(n * math.pi)
        x_hk = BivariateCumulativeStudentDistribution.f_x(n, h, k, rho)
        x_kh = BivariateCumulativeStudentDistribution.f_x(n, k, h, rho)
        div_h = 1 + h * h / n
        div_k = 1 + k * k / n
        sgn_hk = BivariateCumulativeStudentDistribution.sign(h - rho * k)
        sgn_kh = BivariateCumulativeStudentDistribution.sign(k - rho * h)

        if n % 2 == 0:  # n is even, equation (10)
            # first line of (10)
            res = BivariateCumulativeStudentDistribution.arctan(math.sqrt(un_cor), -rho) / (math.pi * 2.0)

            # second line of (10)
            dg_m = 2 * (1 - x_hk)  # multiplier for dgj
            gj_m = sgn_hk * 2 / math.pi  # multiplier for g_j
            # initializations for j = 1:
            f_j = math.sqrt(math.pi / div_k)
            g_j = 1 + gj_m * BivariateCumulativeStudentDistribution.arctan(math.sqrt(x_hk), math.sqrt(1 - x_hk))
            sum_ = f_j * g_j
            if n >= 4:
                # different formulas for j = 2:
                f_j *= 0.5 / div_k  # (2 - 1.5) / (2 - 1) / divK
                dgj = gj_m * math.sqrt(x_hk * (1 - x_hk))
                g_j += dgj
                sum_ += f_j * g_j
                # and then the loop for the rest of the j's:
                j = 3
                while j <= n / 2:
                    f_j *= (j - 1.5) / (j - 1) / div_k
                    dgj *= (j - 2) / (2 * j - 3) * dg_m
                    g_j += dgj
                    sum_ += f_j * g_j
                    j += 1

            res += k / div * sum_

            # third line of (10)
            dg_m = 2 * (1 - x_kh)
            gj_m = sgn_kh * 2 / math.pi
            # initializations for j = 1:
            f_j = math.sqrt(math.pi / div_h)
            g_j = 1 + gj_m * BivariateCumulativeStudentDistribution.arctan(math.sqrt(x_kh), math.sqrt(1 - x_kh))
            sum_ = f_j * g_j
            if n >= 4:
                # different formulas for j = 2:
                f_j *= 0.5 / div_h  # (2 - 1.5) / (2 - 1) / divK
                dgj = gj_m * math.sqrt(x_kh * (1 - x_kh))
                g_j += dgj
                sum_ += f_j * g_j
                # and then the loop for the rest of the j's:
                j = 3
                while j <= n / 2:
                    f_j *= (j - 1.5) / (j - 1) / div_h
                    dgj *= (j - 2) / (2 * j - 3) * dg_m
                    g_j += dgj
                    sum_ += f_j * g_j
                    j += 1

            res += h / div * sum_
            return res

        else:  # n is odd, equation (11)
            # first line of (11)
            hk = h * k
            hkcn = hk + rho * n
            sqrt_expr = math.sqrt(h * h - 2 * rho * hk + k * k + n * un_cor)
            res = BivariateCumulativeStudentDistribution.arctan(math.sqrt(n) * (-(h + k) * hkcn - (hk - n) * sqrt_expr),
                                                                (hk - n) * hkcn - n * (h + k) * sqrt_expr) / (
                              math.pi * 2.0)

            if n > 1:
                # second line of (11)
                mult = (1 - x_hk) / 2
                # initializations for j = 1:
                f_j = 2 / math.sqrt(math.pi) / div_k
                dgj = sgn_hk * math.sqrt(x_hk)
                g_j = 1 + dgj
                sum_ = f_j * g_j
                # and then the loop for the rest of the j's:
                j = 2
                while j <= (n - 1) / 2:
                    f_j *= (j - 1) / (j - 0.5) / div_k
                    dgj *= (2 * j - 3) / (j - 1) * mult
                    g_j += dgj
                    sum_ += f_j * g_j
                    j += 1

                res += k / div * sum_

                # third line of (11)
                mult = (1 - x_kh) / 2
                # initializations for j = 1:
                f_j = 2 / math.sqrt(math.pi) / div_h
                dgj = sgn_kh * math.sqrt(x_kh)
                g_j = 1 + dgj
                sum_ = f_j * g_j
                # and then the loop for the rest of the j's:
                j = 2
                while j <= (n - 1) / 2:
                    f_j *= (j - 1) / (j - 0.5) / div_h
                    dgj *= (2 * j - 3) / (j - 1) * mult
                    g_j += dgj
                    sum_ += f_j * g_j
                    j += 1

                res += h / div * sum_

            return res

    @staticmethod
    def f_x(m, h, k, rho):
        """ function x(m,h,k) defined on top of page 155 """
        un_cor = 1 - rho * rho
        sub = math.pow(h - rho * k, 2)
        denom = sub + un_cor * (m + k * k)
        if denom < BivariateCumulativeStudentDistribution.epsilon:
            return 0.0  # limit case for rho = +/-1.0
        return sub / (sub + un_cor * (m + k * k))

    @staticmethod
    def arctan(x, y):
        """
        unlike the atan2 function in C++ that gives results in
        [-pi,pi], this returns a value in [0, 2*pi]
        :param x:
        :param y:
        :return:
        """
        res = math.atan2(x, y)
        return res if res >= 0.0 else res + 2 * math.pi

    @staticmethod
    def sign(val):
        return 0.0 if val == 0.0 else (-1.0 if val < 0.0 else 1.0)
