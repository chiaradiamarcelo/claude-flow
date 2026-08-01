package com.example.bank.domain.models.account

import java.math.BigDecimal
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class AccountTest {

    @Test
    fun reduces_balance_by_the_withdrawn_amount() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))

        val withdrawn = account.withdraw(BigDecimal("50"))

        assertThat(withdrawn.balance()).isEqualByComparingTo(BigDecimal("150"))
    }

    @Test
    fun allows_withdrawing_the_entire_balance_leaving_zero() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))

        val withdrawn = account.withdraw(BigDecimal("200"))

        assertThat(withdrawn.balance()).isEqualByComparingTo(BigDecimal.ZERO)
    }

    @Test
    fun rejects_a_withdrawal_that_exceeds_the_balance() {
        val account = Account(ACCOUNT_ID, BigDecimal("100"))

        assertThatThrownBy { account.withdraw(BigDecimal("150")) }
            .isInstanceOf(InsufficientFundsException::class.java)
    }

    @Test
    fun rejects_a_zero_withdrawal_amount() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))

        assertThatThrownBy { account.withdraw(BigDecimal.ZERO) }
            .isInstanceOf(InvalidWithdrawalAmountException::class.java)
    }

    @Test
    fun rejects_a_negative_withdrawal_amount() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))

        assertThatThrownBy { account.withdraw(BigDecimal("-50")) }
            .isInstanceOf(InvalidWithdrawalAmountException::class.java)
    }

    @Test
    fun equal_when_account_ids_match() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))
        val sameIdentity = Account(ACCOUNT_ID, BigDecimal("150"))

        assertThat(account).isEqualTo(sameIdentity)
    }

    @Test
    fun not_equal_when_account_ids_differ() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))
        val otherIdentity = Account(OTHER_ACCOUNT_ID, BigDecimal("200"))

        assertThat(account).isNotEqualTo(otherIdentity)
    }
}
