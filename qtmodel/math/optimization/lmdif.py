import math
from typing import Callable, Tuple

import numpy as np
from goto import with_goto, goto, label

from qtmodel.types import Real


# Example of Euclidean norm calculation:
# import numpy as np
#
# dist = np.linalg.norm([4, 5, 6])
# print(dist)

class MINPACK:

    # resolution of arithmetic
    MACHEP = 1.2e-16
    # smallest nonzero number
    DWARF = 1.0e-38

    LmdifCostFunction = Callable[[int, int, list, list, int], None]

    @staticmethod
    def fdjac2(m: int,
               n: int,
               x: list,
               fvec: list,
               fjac: list,
               unnamed_parameter: int,
               iflag: int,
               epsfcn: Real,
               wa: list,
               fcn: LmdifCostFunction):
        zero = 0.0

        temp = max(epsfcn, MINPACK.MACHEP)
        eps = math.sqrt(temp)
        ij = 0
        for j in range(n):
            temp = x[j]
            h = eps * abs(temp)
            if h == zero:
                h = eps
            x[j] = temp + h
            fcn(m, n, x, wa, iflag)
            if iflag < 0:
                return
            x[j] = temp
            for i in range(m):
                fjac[ij] = (wa[i] - fvec[i]) / h
                ij += 1  # fjac[i+m*j]

    @with_goto
    @staticmethod
    def qrfac(m: int,
              n: int,
              a: list,
              unnamed_parameter: int,
              pivot: int,
              ipvt: list,
              unnamed_parameter2: int,
              rdiag: list,
              acnorm: list,
              wa: list):
        zero = 0.0
        one = 1.0
        p05 = 0.05

        ij = 0
        for j in range(n):
            acnorm[j] = np.linalg.norm(a[ij: ij+m])
            rdiag[j] = acnorm[j]
            wa[j] = rdiag[j]
            if pivot != 0:
                ipvt[j] = j
            ij += m  # m * j

        minmn = min(m, n)
        for j in range(minmn):
            if pivot == 0:
                goto.L40

            kmax = j
            for k in range(j, n):
                if rdiag[k] > rdiag[kmax]:
                    kmax = k
            if kmax == j:
                goto.L40

            ij = m * j
            jj = m * kmax
            for i in range(m):
                temp = a[ij]  # [i + m * j]
                a[ij] = a[jj]  # [i + m * kmax]
                a[jj] = temp
                ij += 1
                jj += 1

            rdiag[kmax] = rdiag[j]
            wa[kmax] = wa[j]
            k = ipvt[j]
            ipvt[j] = ipvt[kmax]
            ipvt[kmax] = k

            label.L40
            jj = j + m * j
            ajnorm = np.linalg.norm(a[jj: jj+m-j])
            if ajnorm == zero:
                goto.L100
            if a[jj] < zero:
                ajnorm = -ajnorm
            ij = jj
            for i in range(j, m):
                a[ij] /= ajnorm
                ij += 1  # [i + m * j]
            a[jj] += one

            jp1 = j + 1
            if jp1 < n:
                for k in range(jp1, n):
                    sum = zero
                    ij = j + m * k
                    jj = j + m * j
                    for i in range(j, m):
                        sum += a[jj] * a[ij]
                        ij += 1  # [i + m * k]
                        jj += 1  # [i + m * j]
                    temp = sum / a[j + m * j]
                    ij = j + m * k
                    jj = j + m * j
                    for i in range(j, m):
                        a[ij] -= temp * a[jj]
                        ij += 1  # *[i + m * k]
                        jj += 1  # *[i + m * j]
                    if (pivot != 0) and (rdiag[k] != zero):
                        temp = a[j + m * k] / rdiag[k]
                        temp = max(zero, one - temp * temp)
                        rdiag[k] *= math.sqrt(temp)
                        temp = rdiag[k] / wa[k]
                        if (p05 * temp * temp) <= MINPACK.MACHEP:
                            rdiag[k] = np.linalg.norm(a[jp1+m*k: jp1+m*k+m - j - 1])
                            wa[k] = rdiag[k]

            label.L100
            rdiag[j] = -ajnorm

    @with_goto
    @staticmethod
    def qrsolv(n: int,
               r: list,
               ldr: int,
               ipvt: list,
               diag: list,
               qtb: list,
               x: list,
               sdiag: list,
               wa: list):
        zero = 0.0
        p25 = 0.25
        p5 = 0.5

        kk = 0
        for j in range(n):
            ij = kk
            ik = kk
            for i in range(j, n):
                r[ij] = r[ik]
                ij += 1  # [i + ldr * j]
                ik += ldr  # [j + ldr * i]
            x[j] = r[kk]
            wa[j] = qtb[j]
            kk += ldr + 1  # j + ldr * j

        for j in range(n):
            l = ipvt[j]
            if diag[l] == zero:
                goto.L90
            for k in range(j, n):
                sdiag[k] = zero
            sdiag[j] = diag[l]

            qtbpj = zero
            for k in range(j, n):
                if sdiag[k] == zero:
                    continue
                kk = k + ldr * k
                if abs(r[kk]) < abs(sdiag[k]):
                    cotan = r[kk] / sdiag[k]
                    sin = p5 / math.sqrt(p25 + p25 * cotan * cotan)
                    cos = sin * cotan
                else:
                    tan = sdiag[k] / r[kk]
                    cos = p5 / math.sqrt(p25 + p25 * tan * tan)
                    sin = cos * tan

                r[kk] = cos * r[kk] + sin * sdiag[k]
                temp = cos * wa[k] + sin * qtbpj
                qtbpj = -sin * wa[k] + cos * qtbpj
                wa[k] = temp

                kp1 = k + 1
                if n > kp1:
                    ik = kk + 1
                    for i in range(kp1, n):
                        temp = cos * r[ik] + sin * sdiag[i]
                        sdiag[i] = -sin * r[ik] + cos * sdiag[i]
                        r[ik] = temp
                        ik += 1  # [i + ldr * k]

            label.L90
            kk = j + ldr * j
            sdiag[j] = r[kk]
            r[kk] = x[j]

        nsing = n
        for j in range(n):
            if (sdiag[j] == zero) and (nsing == n):
                nsing = j
            if nsing < n:
                wa[j] = zero
        if nsing < 1:
            goto.L150

        for k in range(nsing):
            j = nsing - k - 1
            sum = zero
            jp1 = j + 1
            if nsing > jp1:
                ij = jp1 + ldr * j
                for i in range(jp1, nsing):
                    sum += r[ij] * wa[i]
                    ij += 1  # [i + ldr * j]
            wa[j] = (wa[j] - sum) / sdiag[j]
        label.L150
        for j in range(n):
            l = ipvt[j]
            x[l] = wa[j]

    @with_goto
    @staticmethod
    def lmpar(n: int,
              r: list,  # n * n
              ldr: int,
              ipvt: list,
              diag: list,
              qtb: list,
              delta: Real,
              par: Real,  # 需要作为函数返回值
              x: list,
              sdiag: list,
              wa1: list,
              wa2: list) -> Real:
        zero = 0.0
        p1 = 0.1
        p001 = 0.001

        nsing = n
        jj = 0
        for j in range(n):
            wa1[j] = qtb[j]
            if (r[jj] == zero) and (nsing == n):
                nsing = j
            if nsing < n:
                wa1[j] = zero
            jj += ldr + 1  # [j + ldr * j]
        if nsing >= 1:
            for k in range(nsing):
                j = nsing - k - 1
                wa1[j] = wa1[j] / r[j + ldr * j]
                temp = wa1[j]
                jm1 = j - 1
                if jm1 >= 0:
                    ij = ldr * j
                    for i in range(jm1+1):
                        wa1[i] -= r[ij] * temp
                        ij += 1

        for j in range(n):
            l = ipvt[j]
            x[l] = wa1[j]

        iter = 0
        for j in range(n):
            wa2[j] = diag[j] * x[j]
        dxnorm = np.linalg.norm(wa2)
        fp = dxnorm - delta
        if fp <= p1 * delta:
            goto.L220

        parl = zero
        if nsing >= n:
            for j in range(n):
                l = ipvt[j]
                wa1[j] = diag[l] * (wa2[l] / dxnorm)
            jj = 0
            for j in range(n):
                sum = zero
                jm1 = j - 1
                if jm1 >= 0:
                    ij = jj
                    for i in range(jm1+1):
                        sum += r[ij] * wa1[i]
                        ij += 1
                wa1[j] = (wa1[j] - sum) / r[j + ldr * j]
                jj += ldr  # [i + ldr * j]
            temp = np.linalg.norm(wa1)
            parl = ((fp / delta) / temp) / temp

        jj = 0
        for j in range(n):
            sum = zero
            ij = jj
            for i in range(j+1):
                sum += r[ij] * qtb[i]
                ij += 1
            l = ipvt[j]
            wa1[j] = sum / diag[l]
            jj += ldr  # [i + ldr * j]

        gnorm = np.linalg.norm(wa1)
        paru = gnorm / delta
        if paru == zero:
            paru = MINPACK.DWARF / min(delta, p1)

        par = max(par, parl)
        par = min(par, paru)
        if par == zero:
            par = gnorm / dxnorm

        label.L150
        iter += 1

        if par == zero:
            par = max(MINPACK.DWARF, p001 * paru)
        temp = math.sqrt(par)
        for j in range(n):
            wa1[j] = temp * diag[j]

        MINPACK.qrsolv(n, r, ldr, ipvt, wa1, qtb, x, sdiag, wa2)

        for j in range(n):
            wa2[j] = diag[j] * x[j]
        dxnorm = np.linalg.norm(wa2)
        temp = fp
        fp = dxnorm - delta

        if (abs(fp) <= p1 * delta) or ((parl == zero) and (fp <= temp) and (temp < zero)) or (iter == 10):
            goto.L220

        for j in range(n):
            l = ipvt[j]
            wa1[j] = diag[l] * (wa2[l] / dxnorm)
        jj = 0
        for j in range(n):
            wa1[j] = wa1[j] / sdiag[j]
            temp = wa1[j]
            jp1 = j + 1
            if jp1 < n:
                ij = jp1 + jj
                for i in range(jp1, n):
                    wa1[i] -= r[ij] * temp
                    ij += 1  # [i + ldr * j]
            jj += ldr  # ldr * j

        temp = np.linalg.norm(wa1)
        parc = ((fp / delta) / temp) / temp

        if fp > zero:
            parl = max(parl, par)
        if fp < zero:
            paru = min(paru, par)

        par = max(parl, par + parc)

        goto.L150

        label.L220
        # termination
        if iter == 0:
            par = zero

        return par

    @with_goto
    @staticmethod
    def lmdif(m: int,
              n: int,
              x: list,
              fvec: list,
              ftol: Real,
              xtol: Real,
              gtol: Real,
              maxfev: int,
              epsfcn: Real,
              diag: list,
              mode: int,
              factor: Real,
              nprint: int,
              info: int,  # 需要作为返回值返回
              nfev: int,  # 需要作为返回值返回
              fjac: list,
              ldfjac: int,
              ipvt: list,
              qtf: list,
              wa1: list,
              wa2: list,
              wa3: list,
              wa4: list,
              fcn: LmdifCostFunction,
              jac_fcn: LmdifCostFunction = None) -> Tuple[int, int]:

        delta = 0
        xnorm = 0

        one = 1.0
        p1 = 0.1
        p5 = 0.5
        p25 = 0.25
        p75 = 0.75
        p0001 = 1.0e-4
        zero = 0.0

        info = 0
        iflag = 0
        nfev = 0

        if ((n <= 0) or (m < n) or (ldfjac < m) or (ftol < zero)
                or (xtol < zero) or (gtol < zero) or (maxfev <= 0)
                or (factor <= zero)):
            goto.L300

        if mode == 2:
            for j in range(n):
                if diag[j] <= 0.0:
                    goto.L300

        iflag = 1
        fcn(m, n, x, fvec, iflag)
        nfev = 1

        if iflag < 0:
            goto.L300
        fnorm = np.linalg.norm(fvec)

        par = zero
        iter = 1

        label.L30
        iflag = 2
        if jac_fcn is None:  # use user supplied jacobian calculation
            MINPACK.fdjac2(m, n, x, fvec, fjac, ldfjac, iflag, epsfcn, wa4, fcn)
        else:
            jac_fcn(m, n, x, fjac, iflag)
        nfev += n
        if iflag < 0:
            goto.L300

        if nprint > 0:
            iflag = 0
            if (iter - 1) % nprint == 0:
                fcn(m, n, x, fvec, iflag)
                if iflag < 0:
                    goto.L300

        MINPACK.qrfac(m, n, fjac, ldfjac, 1, ipvt, n, wa1, wa2, wa3)

        if iter == 1:
            if mode != 2:
                for j in range(n):
                    diag[j] = wa2[j]
                    if wa2[j] == zero:
                        diag[j] = one

            for j in range(n):
                wa3[j] = diag[j] * x[j]

            xnorm = np.linalg.norm(wa3)
            delta = factor * xnorm
            if delta == zero:
                delta = factor

        for i in range(m):
            wa4[i] = fvec[i]
        jj = 0
        for j in range(n):
            temp3 = fjac[jj]
            if temp3 != zero:
                sum = zero
                ij = jj
                for i in range(j, m):
                    sum += fjac[ij] * wa4[i]
                    ij += 1  # fjac[i + m * j]
                temp = -sum / temp3
                ij = jj
                for i in range(j, m):
                    wa4[i] += fjac[ij] * temp
                    ij += 1  # fjac[i + m * j]
            fjac[jj] = wa1[j]
            jj += m + 1  # fjac[j + m * j]
            qtf[j] = wa4[j]

        gnorm = zero
        if fnorm != zero:
            jj = 0
            for j in range(n):
                l = ipvt[j]
                if wa2[l] != zero:
                    sum = zero
                    ij = jj
                    for i in range(j+1):
                        sum += fjac[ij] * (qtf[i] / fnorm)
                        ij += 1  # fjac[i + m * j]
                    gnorm = max(gnorm, abs(sum / wa2[l]))
                jj += m

        if gnorm <= gtol:
            info = 4
        if info != 0:
            goto.L300

        if mode != 2:
            for j in range(n):
                diag[j] = max(diag[j], wa2[j])

        label.L200
        par = MINPACK.lmpar(n, fjac, ldfjac, ipvt, diag, qtf, delta, par, wa1, wa2, wa3, wa4)

        for j in range(n):
            wa1[j] = -wa1[j]
            wa2[j] = x[j] + wa1[j]
            wa3[j] = diag[j] * wa1[j]

        pnorm = np.linalg.norm(wa3)

        if iter == 1:
            delta = min(delta, pnorm)

        iflag = 1
        fcn(m, n, wa2, wa4, iflag)
        nfev += 1
        if iflag < 0:
            goto.L300
        fnorm1 = np.linalg.norm(wa4)

        actred = -one
        if (p1 * fnorm1) < fnorm:
            temp = fnorm1 / fnorm
            actred = one - temp * temp

        jj = 0
        for j in range(n):
            wa3[j] = zero
            l = ipvt[j]
            temp = wa1[l]
            ij = jj
            for i in range(j+1):
                wa3[i] += fjac[ij] * temp
                ij += 1  # fjac[i + m * j]
            jj += m
        temp1 = np.linalg.norm(wa3) / fnorm
        temp2 = (math.sqrt(par) * pnorm) / fnorm
        prered = temp1 * temp1 + (temp2 * temp2) / p5
        dirder = -(temp1 * temp1 + temp2 * temp2)

        ratio = zero
        if prered != zero:
            ratio = actred / prered

        if ratio <= p25:
            if actred >= zero:
                temp = p5
            else:
                temp = p5 * dirder / (dirder + p5 * actred)
            if ((p1 * fnorm1) >= fnorm) or (temp < p1):
                temp = p1
            delta = temp * min(delta, pnorm / p1)
            par = par / temp
        else:
            if (par == zero) or (ratio >= p75):
                delta = pnorm / p5
                par *= p5

        if ratio >= p0001:
            for j in range(n):
                x[j] = wa2[j]
                wa2[j] = diag[j] * x[j]
            for i in range(m):
                fvec[i] = wa4[i]
            xnorm = np.linalg.norm(wa2)
            fnorm = fnorm1
            iter += 1

        if (abs(actred) <= ftol) and (prered <= ftol) and (p5 * ratio <= one):
            info = 1
        if delta <= xtol * xnorm:
            info = 2
        if (abs(actred) <= ftol) and (prered <= ftol) and (p5 * ratio <= one) and (info == 2):
            info = 3
        if info != 0:
            goto.L300

        if nfev >= maxfev:
            info = 5
        if (abs(actred) <= MINPACK.MACHEP) and (prered <= MINPACK.MACHEP) and (p5 * ratio <= one):
            info = 6
        if delta <= MINPACK.MACHEP * xnorm:
            info = 7
        if gnorm <= MINPACK.MACHEP:
            info = 8
        if info != 0:
            goto.L300

        if ratio < p0001:
            goto.L200

        goto.L30

        label.L300
        if iflag < 0:
            info = iflag
        iflag = 0
        if nprint > 0:
            fcn(m, n, x, fvec, iflag)

        return info, nfev



