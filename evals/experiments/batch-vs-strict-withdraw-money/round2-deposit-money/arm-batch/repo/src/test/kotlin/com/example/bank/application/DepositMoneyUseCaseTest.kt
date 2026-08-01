package com.example.bank.application

import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountNotFoundException
import com.example.bank.domain.models.account.InvalidDepositAmountException
import com.example.bank.domain.models.account.fakes.FakeAccountRepository
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.assertj.core.api.ThrowableAssert.ThrowingCallable
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import java.math.BigDecimal

private const val ACCOUNT_ID = "ACC-001"
private const val UNKNOWN_ACCOUNT_ID = "ACC-404"

class DepositMoneyUseCaseTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var depositMoney: DepositMoneyUseCase

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        depositMoney = DepositMoneyUseCase(accounts)
    }

    @Test
    fun increases_the_returned_balance_by_the_deposited_amount_when_the_account_exists() {
        accounts.seed(Account(ACCOUNT_ID, BigDecimal("200")))

        val updated = depositMoney.deposit(ACCOUNT_ID, BigDecimal("50"))

        assertThat(updated.balance).isEqualByComparingTo(BigDecimal("250"))
    }

    @Test
    fun persists_the_increased_balance_when_the_account_exists() {
        accounts.seed(Account(ACCOUNT_ID, BigDecimal("200")))

        depositMoney.deposit(ACCOUNT_ID, BigDecimal("50"))

        assertThat(accounts.findById(ACCOUNT_ID)?.balance).isEqualByComparingTo(BigDecimal("250"))
    }

    @Test
    fun fails_when_the_deposit_amount_is_not_positive() {
        accounts.seed(Account(ACCOUNT_ID, BigDecimal("200")))

        val depositingZero = ThrowingCallable { depositMoney.deposit(ACCOUNT_ID, BigDecimal.ZERO) }

        assertThatThrownBy(depositingZero).isInstanceOf(InvalidDepositAmountException::class.java)
    }

    @Test
    fun fails_when_the_account_does_not_exist() {
        val depositingIntoAnUnknownAccount = ThrowingCallable { depositMoney.deposit(UNKNOWN_ACCOUNT_ID, BigDecimal("50")) }

        assertThatThrownBy(depositingIntoAnUnknownAccount).isInstanceOf(AccountNotFoundException::class.java)
    }
}
