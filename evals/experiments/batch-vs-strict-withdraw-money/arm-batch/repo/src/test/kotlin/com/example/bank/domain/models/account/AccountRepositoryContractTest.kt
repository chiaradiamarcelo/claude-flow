package com.example.bank.domain.models.account

import java.math.BigDecimal
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

/**
 * Behavioural contract every [AccountRepository] implementation must satisfy.
 * Abstract on purpose: it runs only through the implementation specs.
 */
abstract class AccountRepositoryContractTest {

    private lateinit var repository: AccountRepository

    protected abstract fun newRepository(): AccountRepository

    @BeforeEach
    fun createRepository() {
        repository = newRepository()
    }

    @Test
    fun save_then_find_by_id_returns_the_saved_account() {
        repository.save(Account(ACCOUNT_ID, BigDecimal("200")))

        val found = repository.findById(ACCOUNT_ID)

        assertThat(found).isEqualTo(Account(ACCOUNT_ID, BigDecimal("200")))
        assertThat(found?.balance()).isEqualByComparingTo(BigDecimal("200"))
    }

    @Test
    fun find_by_id_returns_empty_when_no_account_exists() {
        val found = repository.findById(MISSING_ACCOUNT_ID)

        assertThat(found).isNull()
    }

    @Test
    fun save_overwrites_the_existing_account_for_the_same_id() {
        repository.save(Account(ACCOUNT_ID, BigDecimal("200")))
        repository.save(Account(ACCOUNT_ID, BigDecimal("150")))

        val found = repository.findById(ACCOUNT_ID)

        assertThat(found?.balance()).isEqualByComparingTo(BigDecimal("150"))
    }
}
