package com.example.bank.domain.models.account

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.math.BigDecimal

class AccountTest {

    @Test
    fun accounts_with_the_same_id_are_equal_regardless_of_balance() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))
        val sameAccountWithADifferentBalance = Account(ACCOUNT_ID, BigDecimal("250"))

        val equal = account == sameAccountWithADifferentBalance

        assertThat(equal).isTrue()
    }

    @Test
    fun accounts_with_different_ids_are_not_equal() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))
        val otherAccount = Account(OTHER_ACCOUNT_ID, BigDecimal("200"))

        val equal = account == otherAccount

        assertThat(equal).isFalse()
    }
}

private const val ACCOUNT_ID = "ACC-001"
private const val OTHER_ACCOUNT_ID = "ACC-002"
