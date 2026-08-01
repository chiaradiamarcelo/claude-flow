package com.example.bank.domain.query

import java.math.BigDecimal

data class AccountOverviewView(
    val accountId: String,
    val balance: BigDecimal,
    val tier: AccountTier,
)
