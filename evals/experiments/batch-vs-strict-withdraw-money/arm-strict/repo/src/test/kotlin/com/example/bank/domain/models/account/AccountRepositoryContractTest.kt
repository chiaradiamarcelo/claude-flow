package com.example.bank.domain.models.account

import org.assertj.core.api.Assertions.assertThat
import java.math.BigDecimal
import kotlin.test.Test

abstract class AccountRepositoryContractTest {

    protected abstract val repository: AccountRepository

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

private const val ACCOUNT_ID = "ACC-001"
private const val MISSING_ACCOUNT_ID = "MISSING"
