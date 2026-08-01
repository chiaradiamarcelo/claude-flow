package com.example.bank.domain.query

import java.math.BigDecimal
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class AccountTierTest {

    @Test
    fun returns_STANDARD_when_balance_is_below_1000() {
        val tier = AccountTier.forBalance(BigDecimal("999"))

        assertThat(tier).isEqualTo(AccountTier.STANDARD)
    }

    @Test
    fun returns_PREMIUM_when_balance_is_above_1000() {
        val tier = AccountTier.forBalance(BigDecimal("1500"))

        assertThat(tier).isEqualTo(AccountTier.PREMIUM)
    }

    @Test
    fun returns_PREMIUM_when_balance_is_exactly_1000() {
        val tier = AccountTier.forBalance(BigDecimal("1000"))

        assertThat(tier).isEqualTo(AccountTier.PREMIUM)
    }
}
