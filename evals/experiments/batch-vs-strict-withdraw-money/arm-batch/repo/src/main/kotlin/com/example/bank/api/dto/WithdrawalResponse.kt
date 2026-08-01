package com.example.bank.api.dto

import java.math.BigDecimal

data class WithdrawalResponse(val accountId: String, val balance: BigDecimal)
