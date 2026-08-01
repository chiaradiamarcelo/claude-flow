package com.example.bank.domain.models.account

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.math.BigDecimal

const val CONTRACT_ACCOUNT_ID = "ACC-001"

/**
 * Behavioural contract every [AccountRepository] implementation must satisfy.
 * Never run directly — executed through each implementation's own spec.
 */
abstract class AccountRepositoryContract {

    protected abstract val repository: AccountRepository

    @Test
    fun save_then_findById_returns_the_stored_account_with_its_balance() {
        repository.save(Account(CONTRACT_ACCOUNT_ID, BigDecimal("200")))

        val found = repository.findById(CONTRACT_ACCOUNT_ID)

        assertThat(found?.accountId).isEqualTo(CONTRACT_ACCOUNT_ID)
        assertThat(found?.balance).isEqualByComparingTo(BigDecimal("200"))
    }

    @Test
    fun findById_returns_null_when_no_account_is_stored() {
        val found = repository.findById(CONTRACT_ACCOUNT_ID)

        assertThat(found).isNull()
    }

    @Test
    fun save_updates_the_balance_of_an_existing_account() {
        repository.save(Account(CONTRACT_ACCOUNT_ID, BigDecimal("200")))
        repository.save(Account(CONTRACT_ACCOUNT_ID, BigDecimal("250")))

        val found = repository.findById(CONTRACT_ACCOUNT_ID)

        assertThat(found?.balance).isEqualByComparingTo(BigDecimal("250"))
    }
}
