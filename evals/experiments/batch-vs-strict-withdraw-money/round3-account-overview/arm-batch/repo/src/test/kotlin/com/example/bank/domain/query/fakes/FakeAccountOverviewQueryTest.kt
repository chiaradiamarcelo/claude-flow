package com.example.bank.domain.query.fakes

import com.example.bank.domain.query.AccountOverviewQuery
import com.example.bank.domain.query.AccountOverviewQueryContract
import com.example.bank.domain.query.AccountOverviewView
import com.example.bank.domain.query.AccountTier
import java.math.BigDecimal
import org.junit.jupiter.api.BeforeEach

class FakeAccountOverviewQueryTest : AccountOverviewQueryContract() {

    private lateinit var fake: FakeAccountOverviewQuery

    override val query: AccountOverviewQuery
        get() = fake

    @BeforeEach
    fun setUp() {
        fake = FakeAccountOverviewQuery()
    }

    override fun seedAccount(accountId: String, balance: BigDecimal) {
        fake.seed(AccountOverviewView(accountId, balance, AccountTier.forBalance(balance)))
    }
}
