package com.example.bank.application

import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountNotFoundException
import com.example.bank.domain.models.account.fakes.FakeAccountRepository
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.catchThrowable
import org.junit.jupiter.api.BeforeEach
import java.math.BigDecimal
import kotlin.test.Test

class WithdrawMoneyUseCaseTest {

    private lateinit var accountRepository: FakeAccountRepository
    private lateinit var withdrawMoney: WithdrawMoneyUseCase

    @BeforeEach
    fun setUp() {
        accountRepository = FakeAccountRepository()
        withdrawMoney = WithdrawMoneyUseCase(accountRepository)
    }

    @Test
    fun withdraws_the_requested_amount_and_returns_the_updated_account() {
        accountRepository.save(Account(ACCOUNT_ID, BigDecimal("200")))

        val updated = withdrawMoney.execute(ACCOUNT_ID, BigDecimal("50"))

        assertThat(updated.balance()).isEqualByComparingTo(BigDecimal("150"))
    }

    @Test
    fun persists_the_updated_account() {
        accountRepository.save(Account(ACCOUNT_ID, BigDecimal("200")))

        withdrawMoney.execute(ACCOUNT_ID, BigDecimal("50"))

        assertThat(accountRepository.findById(ACCOUNT_ID)?.balance()).isEqualByComparingTo(BigDecimal("150"))
    }

    @Test
    fun fails_when_no_account_exists_for_the_id() {
        val thrown = catchThrowable { withdrawMoney.execute(MISSING_ACCOUNT_ID, BigDecimal("50")) }

        assertThat(thrown).isInstanceOf(AccountNotFoundException::class.java)
    }
}

private const val ACCOUNT_ID = "ACC-001"
private const val MISSING_ACCOUNT_ID = "MISSING"
