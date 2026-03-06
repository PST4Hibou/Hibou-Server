import numpy as np
import numpy.typing as npt

type GSTtimestamp = int
type GstChannel = list[npt.NDArray[float, GSTtimestamp]]
