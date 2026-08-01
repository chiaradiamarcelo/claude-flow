package com.example.bank.api.dto

import com.example.bank.domain.query.AccountTier
import java.math.BigDecimal

data class AccountOverviewResponse(
    val accountId: String,
    val balance: BigDecimal,
    val tier: AccountTier,
)
