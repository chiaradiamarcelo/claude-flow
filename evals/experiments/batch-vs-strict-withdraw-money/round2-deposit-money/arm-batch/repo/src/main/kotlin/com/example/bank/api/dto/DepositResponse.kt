package com.example.bank.api.dto

import java.math.BigDecimal

data class DepositResponse(val accountId: String, val balance: BigDecimal)
