package com.example.bank.domain.query

import java.math.BigDecimal

enum class AccountTier {
    STANDARD,
    PREMIUM;

    companion object {
        private val PREMIUM_THRESHOLD: BigDecimal = BigDecimal("1000")

        fun forBalance(balance: BigDecimal): AccountTier =
            if (isAtLeastPremiumThreshold(balance)) PREMIUM else STANDARD

        private fun isAtLeastPremiumThreshold(balance: BigDecimal): Boolean =
            balance >= PREMIUM_THRESHOLD
    }
}
