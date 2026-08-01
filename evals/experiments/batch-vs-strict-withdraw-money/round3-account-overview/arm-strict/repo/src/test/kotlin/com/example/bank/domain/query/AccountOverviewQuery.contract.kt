package com.example.bank.domain.query

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.math.BigDecimal

const val ACC_001 = "ACC-001"
const val MISSING_ID = "ACC-999"
val PREMIUM_BALANCE: BigDecimal = BigDecimal("1500")

abstract class AccountOverviewQueryContract {

    protected abstract fun query(): AccountOverviewQuery

    protected abstract fun persistAccount(accountId: String, balance: BigDecimal)

    @Test
    fun returns_the_full_overview_for_a_persisted_account() {
        persistAccount(ACC_001, PREMIUM_BALANCE)

        val overview = query().findByAccountId(ACC_001)

        assertThat(overview)
            .usingRecursiveComparison()
            .withComparatorForType(Comparator.naturalOrder<BigDecimal>(), BigDecimal::class.java)
            .isEqualTo(AccountOverviewView("ACC-001", BigDecimal("1500"), AccountTier.PREMIUM))
    }

    @Test
    fun returns_null_when_no_account_has_the_id() {
        persistAccount(ACC_001, PREMIUM_BALANCE)

        val overview = query().findByAccountId(MISSING_ID)

        assertThat(overview).isNull()
    }
}
