import numpy as np
import math
from fractions import Fraction
from sympy import Matrix
from latex_printing import sympy2tex
from IPython.display import Latex
import scipy

def _num_to_latex(num, precision=10):
    """Takes a complex number as input and returns a latex representation

    Args:
        num (numerical): The number to be converted to latex.
        precision (int): If the real or imaginary parts of num are not close
                         to an integer, the number of decimal places to round to

    Returns:
        str: Latex representation of num
    """
    # Result is combination of maximum 4 strings in the form:
    #     {common_facstring} ( {realstring} {operation} {imagstring}i )
    # common_facstring: A common factor between the real and imaginary part
    # realstring: The real part (inc. a negative sign if applicable)
    # operation: The operation between the real and imaginary parts ('+' or '-')
    # imagstring: Absolute value of the imaginary parts (i.e. not inc. any negative sign).
    # This function computes each of these strings and combines appropriately.

    r = np.real(num)
    i = np.imag(num)
    common_factor = None

    # try to factor out common terms in imaginary numbers
    if np.isclose(abs(r), abs(i)) and not np.isclose(r, 0) and not np.isclose(i, 0):
        common_factor = abs(r)
        r = r / common_factor
        i = i / common_factor

    common_terms = {
        1 / math.sqrt(2): "\\tfrac{1}{\\sqrt{2}}",
        1 / math.sqrt(3): "\\tfrac{1}{\\sqrt{3}}",
        math.sqrt(2 / 3): "\\sqrt{\\tfrac{2}{3}}",
        math.sqrt(3 / 4): "\\sqrt{\\tfrac{3}{4}}",
        1 / math.sqrt(8): "\\tfrac{1}{\\sqrt{8}}",
    }

    def _proc_value(val):
        # This function converts a real value to a latex string
        # First, see if val is close to an integer:
        val_mod = np.mod(val, 1)
        if np.isclose(val_mod, 0) or np.isclose(val_mod, 1):
            # If so, return that integer
            return str(int(np.round(val)))
        # Otherwise, see if it matches one of the common terms
        for term, latex_str in common_terms.items():
            if np.isclose(abs(val), term):
                if val > 0:
                    return latex_str
                else:
                    return "-" + latex_str
        # try to factorise val nicely
        frac = Fraction(val).limit_denominator(1000)
        num, denom = frac.numerator, frac.denominator
        if round((num/denom)*(10**precision)) == round(val*(10**precision)):
          if abs(num) + abs(denom) < 1000:
              # If fraction is 'nice' return
              if val > 0:
                  return f"\\tfrac{{{abs(num)}}}{{{abs(denom)}}}"
              else:
                  return f"-\\tfrac{{{abs(num)}}}{{{abs(denom)}}}"
          else:
            # Failing everything else, return val as a decimal
            return "{:.{}f}".format(val, precision).rstrip("0")
        else:
            # Failing everything else, return val as a decimal
            return "{:.{}f}".format(val, precision).rstrip("0")

    # Get string (or None) for common factor between real and imag
    if common_factor is None:
        common_facstring = None
    else:
        common_facstring = _proc_value(common_factor)

    # Get string for real part
    realstring = _proc_value(r)

    # Get string for both imaginary part and operation between real and imaginary parts
    if i > 0:
        operation = "+"
        imagstring = _proc_value(i)
    else:
        operation = "-"
        imagstring = _proc_value(-i)
    if imagstring == "1":
        imagstring = ""  # Don't want to return '1i', just 'i'

    # Now combine the strings appropriately:
    if imagstring == "0":
        return realstring  # realstring already contains the negative sign (if needed)
    if realstring == "0":
        # imagstring needs the negative sign adding
        if operation == "-":
            return f"-{imagstring}i"
        else:
            return f"{imagstring}i"
    if common_facstring is not None:
        return f"{common_facstring}({realstring} {operation} {imagstring}i)"
    else:
        return f"{realstring} {operation} {imagstring}i"

def _matrix_to_latex(matrix, precision=10, prefix="", max_size=(8, 8)):
    """Latex representation of a complex numpy array (with maximum dimension 2)

    Args:
        matrix (ndarray): The matrix to be converted to latex, must have dimension 2.
        precision (int): For numbers not close to integers, the number of decimal places
                         to round to.
        prefix (str): Latex string to be prepended to the latex, intended for labels.
        max_size (list(```int```)): Indexable containing two integers: Maximum width and maximum
                          height of output Latex matrix (including dots characters). If the
                          width and/or height of matrix exceeds the maximum, the centre values
                          will be replaced with dots. Maximum width or height must be greater
                          than 3.

    Returns:
        str: Latex representation of the matrix

    Raises:
        ValueError: If minimum value in max_size < 3
    """
    if min(max_size) < 3:
        raise ValueError("""Smallest value in max_size must be greater than or equal to 3""")

    out_string = f"\n{prefix}\n"
    out_string += "\\begin{bmatrix}\n"

    def _elements_to_latex(elements):
        # Takes a list of elements (a row) and creates a latex
        # string from it; Each element separated by `&`
        el_string = ""
        for el in elements:
            num_string = _num_to_latex(el, precision=precision)
            el_string += num_string + " & "
        el_string = el_string[:-2]  # remove trailing ampersands
        return el_string

    def _rows_to_latex(rows, max_width):
        # Takes a list of lists (list of 'rows') and creates a
        # latex string from it
        row_string = ""
        for r in rows:
            if len(r) <= max_width:
                row_string += _elements_to_latex(r)
            else:
                row_string += _elements_to_latex(r[: max_width // 2])
                row_string += "& \\cdots & "
                row_string += _elements_to_latex(r[-max_width // 2 + 1 :])
            row_string += " \\\\\n "
        return row_string

    max_width, max_height = max_size
    if matrix.ndim == 1:
        out_string += _rows_to_latex([matrix], max_width)

    elif len(matrix) > max_height:
        # We need to truncate vertically, so we process the rows at the beginning
        # and end, and add a line of vertical elipse (dots) characters between them
        out_string += _rows_to_latex(matrix[: max_height // 2], max_width)

        if max_width >= matrix.shape[1]:
            out_string += "\\vdots & " * matrix.shape[1]
        else:
            # In this case we need to add the diagonal dots in line with the column
            # of horizontal dots
            pre_vdots = max_width // 2
            post_vdots = max_width // 2 + np.mod(max_width, 2) - 1
            out_string += "\\vdots & " * pre_vdots
            out_string += "\\ddots & "
            out_string += "\\vdots & " * post_vdots

        out_string = out_string[:-2] + "\\\\\n "
        out_string += _rows_to_latex(matrix[-max_height // 2 + 1 :], max_width)

    else:
        out_string += _rows_to_latex(matrix, max_width)
    out_string += "\\end{bmatrix}\n"
    return out_string

def a2l(array=None, prefix="", precision=10, source=False, max_size=8):
    if array is None:
      from IPython.display import Latex
      return Latex(f"$${prefix}$$")
    try:
        array = np.asarray(array)
        _ = array[0] + 1  # Test first element contains numerical data
    except TypeError as err:
        raise TypeError(
            """array_to_latex can only convert numpy arrays containing numerical data,
        or types that can be converted to such arrays"""
        ) from err

    if array.ndim <= 2:
        if isinstance(max_size, int):
            max_size = (max_size, max_size)
        outstr = _matrix_to_latex(array, precision=precision, prefix=prefix, max_size=max_size)
    else:
        raise ValueError("array_to_latex can only convert numpy ndarrays of dimension 1 or 2")

    if source is False:
        from IPython.display import Latex
        return Latex(f"$${outstr}$$")
    else:
        return outstr

def normalize(x):
    n = math.sqrt(sum([x[i]*x[i] for i in range(0, len(x))]))
    return x/n

# Find LU decomposition with: L, U, _ = A.LUdecomposition()