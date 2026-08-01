package com.example.bank.domain.query

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.math.BigDecimal

class AccountTierTest {

    @Test
    fun returns_STANDARD_when_balance_is_below_1000() {
        val balance = BigDecimal("999")

        val tier = AccountTier.forBalance(balance)

        assertThat(tier).isEqualTo(AccountTier.STANDARD)
    }

    @Test
    fun returns_PREMIUM_when_balance_is_above_1000() {
        val balance = BigDecimal("1500")

        val tier = AccountTier.forBalance(balance)

        assertThat(tier).isEqualTo(AccountTier.PREMIUM)
    }

    @Test
    fun returns_PREMIUM_when_balance_is_exactly_1000() {
        val balance = BigDecimal("1000")

        val tier = AccountTier.forBalance(balance)

        assertThat(tier).isEqualTo(AccountTier.PREMIUM)
    }
}
