package com.example.bank.domain.query

import java.math.BigDecimal

enum class AccountTier {
    STANDARD,
    PREMIUM;

    companion object {
        private val PREMIUM_THRESHOLD = BigDecimal("1000")

        fun forBalance(balance: BigDecimal): AccountTier =
            if (balance >= PREMIUM_THRESHOLD) PREMIUM else STANDARD
    }
}
