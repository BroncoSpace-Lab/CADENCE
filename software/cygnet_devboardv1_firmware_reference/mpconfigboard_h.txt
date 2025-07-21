// This file is part of the CircuitPython project: https://circuitpython.org
//
// SPDX-FileCopyrightText: Copyright (c) 2024 Adafruit Industries LLC
//
// SPDX-License-Identifier: MIT

#pragma once

#define MICROPY_HW_BOARD_NAME "Cygnet Dev Board v1"
#define MICROPY_HW_MCU_NAME "rp2040"

#define CIRCUITPY_DRIVE_LABEL "Cygnet"

#define DEFAULT_I2C_BUS_SCL (&pin_GPIO5)
#define DEFAULT_I2C_BUS_SDA (&pin_GPIO4)

#define DEFAULT_SPI_BUS_SCK (&pin_GPIO2)
#define DEFAULT_SPI_BUS_MOSI (&pin_GPIO3)
#define DEFAULT_SPI_BUS_MISO (&pin_GPIO0)

#define DEFAULT_UART_BUS_RX (&pin_GPIO9)
#define DEFAULT_UART_BUS_TX (&pin_GPIO8)
