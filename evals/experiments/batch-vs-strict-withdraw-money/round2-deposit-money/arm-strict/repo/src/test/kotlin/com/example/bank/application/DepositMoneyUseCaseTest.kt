package com.example.bank.application

import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountNotFoundException
import com.example.bank.domain.models.account.InvalidDepositAmountException
import com.example.bank.domain.models.account.fakes.FakeAccountRepository
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.catchThrowable
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import java.math.BigDecimal

class DepositMoneyUseCaseTest {

    private lateinit var accountRepository: FakeAccountRepository
    private lateinit var depositMoney: DepositMoneyUseCase

    @BeforeEach
    fun setUp() {
        accountRepository = FakeAccountRepository()
        depositMoney = DepositMoneyUseCase(accountRepository)
    }

    @Test
    fun increases_the_returned_balance_by_the_deposited_amount_when_the_account_exists() {
        accountRepository.seed(Account(ACCOUNT_ID, BigDecimal("200")))

        val account = depositMoney.deposit(ACCOUNT_ID, BigDecimal("50"))

        assertThat(account.balance).isEqualByComparingTo(BigDecimal("250"))
    }

    @Test
    fun persists_the_increased_balance_when_the_account_exists() {
        accountRepository.seed(Account(ACCOUNT_ID, BigDecimal("200")))

        depositMoney.deposit(ACCOUNT_ID, BigDecimal("50"))

        assertThat(accountRepository.findById(ACCOUNT_ID)!!.balance).isEqualByComparingTo(BigDecimal("250"))
    }

    @Test
    fun fails_when_the_deposit_amount_is_not_positive() {
        accountRepository.seed(Account(ACCOUNT_ID, BigDecimal("200")))

        val thrown = catchThrowable { depositMoney.deposit(ACCOUNT_ID, BigDecimal.ZERO) }

        assertThat(thrown).isInstanceOf(InvalidDepositAmountException::class.java)
    }

    @Test
    fun fails_when_the_account_does_not_exist() {
        val thrown = catchThrowable { depositMoney.deposit(UNKNOWN_ACCOUNT_ID, BigDecimal("50")) }

        assertThat(thrown).isInstanceOf(AccountNotFoundException::class.java)
    }
}

private const val ACCOUNT_ID = "ACC-001"
private const val UNKNOWN_ACCOUNT_ID = "ACC-404"
