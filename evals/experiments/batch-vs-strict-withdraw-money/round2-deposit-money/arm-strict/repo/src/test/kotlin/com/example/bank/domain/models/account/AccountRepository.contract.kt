package com.example.bank.domain.models.account

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.math.BigDecimal

abstract class AccountRepositoryContract {

    protected abstract val accountRepository: AccountRepository

    @Test
    fun save_then_findById_returns_the_stored_account_with_its_balance() {
        accountRepository.save(Account(ACCOUNT_ID, BigDecimal("200")))

        val found = accountRepository.findById(ACCOUNT_ID)!!

        assertThat(found.accountId).isEqualTo(ACCOUNT_ID)
        assertThat(found.balance).isEqualByComparingTo(BigDecimal("200"))
    }

    @Test
    fun findById_returns_null_when_no_account_is_stored() {
        val found = accountRepository.findById(ACCOUNT_ID)

        assertThat(found).isNull()
    }

    @Test
    fun save_updates_the_balance_of_an_existing_account() {
        accountRepository.save(Account(ACCOUNT_ID, BigDecimal("200")))
        accountRepository.save(Account(ACCOUNT_ID, BigDecimal("250")))

        val found = accountRepository.findById(ACCOUNT_ID)!!

        assertThat(found.balance).isEqualByComparingTo(BigDecimal("250"))
    }

    private companion object {
        const val ACCOUNT_ID = "ACC-001"
    }
}
