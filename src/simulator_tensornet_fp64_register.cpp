/*******************************************************************************
 * Copyright (c) 2022 - 2025 NVIDIA Corporation & Affiliates.                  *
 * All rights reserved.                                                        *
 *                                                                             *
 * This source code and the accompanying materials are made available under    *
 * the terms of the Apache License 2.0 which accompanies this distribution.    *
 ******************************************************************************/

#include "simulator_tensornet.h"

/// Register this Simulator class with NVQIR under name "formotensor"
NVQIR_REGISTER_SIMULATOR(nvqir::SimulatorTensorNet<double>, formotensor)
