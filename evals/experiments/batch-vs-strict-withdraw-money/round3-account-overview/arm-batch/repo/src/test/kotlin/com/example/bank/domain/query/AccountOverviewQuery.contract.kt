package com.example.bank.domain.query

import java.math.BigDecimal
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

const val ACC_001 = "ACC-001"
const val MISSING_ID = "ACC-999"
val PREMIUM_BALANCE: BigDecimal = BigDecimal("1500")

/**
 * Behavioural contract every [AccountOverviewQuery] implementation must satisfy.
 * Run by [com.example.bank.domain.query.fakes.FakeAccountOverviewQueryTest] and by the
 * real JPA adapter's integration spec. Abstract, so it is never executed on its own.
 */
abstract class AccountOverviewQueryContract {

    protected abstract val query: AccountOverviewQuery

    protected abstract fun seedAccount(accountId: String, balance: BigDecimal)

    @Test
    fun returns_the_full_overview_for_a_persisted_account() {
        seedAccount(ACC_001, PREMIUM_BALANCE)

        val overview = query.findByAccountId(ACC_001)

        assertThat(overview)
            .usingRecursiveComparison()
            .withComparatorForType(Comparator.naturalOrder<BigDecimal>(), BigDecimal::class.java)
            .isEqualTo(AccountOverviewView("ACC-001", BigDecimal("1500"), AccountTier.PREMIUM))
    }

    @Test
    fun returns_null_when_no_account_has_the_id() {
        seedAccount(ACC_001, PREMIUM_BALANCE)

        val overview = query.findByAccountId(MISSING_ID)

        assertThat(overview).isNull()
    }
}
