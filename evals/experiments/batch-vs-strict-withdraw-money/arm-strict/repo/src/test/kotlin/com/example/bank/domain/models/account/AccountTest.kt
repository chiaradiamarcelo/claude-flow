package com.example.bank.domain.models.account

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.catchThrowable
import java.math.BigDecimal
import kotlin.test.Test

class AccountTest {

    @Test
    fun reduces_balance_by_the_withdrawn_amount() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))

        val updated = account.withdraw(BigDecimal("50"))

        assertThat(updated.balance()).isEqualByComparingTo(BigDecimal("150"))
    }

    @Test
    fun allows_withdrawing_the_entire_balance_leaving_zero() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))

        val updated = account.withdraw(BigDecimal("200"))

        assertThat(updated.balance()).isEqualByComparingTo(BigDecimal.ZERO)
    }

    @Test
    fun rejects_a_withdrawal_that_exceeds_the_balance() {
        val account = Account(ACCOUNT_ID, BigDecimal("100"))

        val thrown = catchThrowable { account.withdraw(BigDecimal("150")) }

        assertThat(thrown).isInstanceOf(InsufficientFundsException::class.java)
    }

    @Test
    fun rejects_a_zero_withdrawal_amount() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))

        val thrown = catchThrowable { account.withdraw(BigDecimal.ZERO) }

        assertThat(thrown).isInstanceOf(InvalidWithdrawalAmountException::class.java)
    }

    @Test
    fun rejects_a_negative_withdrawal_amount() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))

        val thrown = catchThrowable { account.withdraw(BigDecimal("-50")) }

        assertThat(thrown).isInstanceOf(InvalidWithdrawalAmountException::class.java)
    }

    @Test
    fun equal_when_account_ids_match() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))

        val sameAccountWithAnotherBalance = Account(ACCOUNT_ID, BigDecimal("150"))

        assertThat(account).isEqualTo(sameAccountWithAnotherBalance)
    }

    @Test
    fun not_equal_when_account_ids_differ() {
        val account = Account(ACCOUNT_ID, BigDecimal("200"))

        val otherAccountWithSameBalance = Account(OTHER_ACCOUNT_ID, BigDecimal("200"))

        assertThat(account).isNotEqualTo(otherAccountWithSameBalance)
    }
}

private const val ACCOUNT_ID = "ACC-001"
private const val OTHER_ACCOUNT_ID = "ACC-002"
