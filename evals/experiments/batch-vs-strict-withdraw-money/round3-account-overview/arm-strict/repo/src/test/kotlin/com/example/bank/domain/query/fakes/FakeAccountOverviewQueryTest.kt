package com.example.bank.domain.query.fakes

import com.example.bank.domain.query.AccountOverviewQuery
import com.example.bank.domain.query.AccountOverviewQueryContract
import com.example.bank.domain.query.AccountOverviewView
import com.example.bank.domain.query.AccountTier
import org.junit.jupiter.api.BeforeEach
import java.math.BigDecimal

class FakeAccountOverviewQueryTest : AccountOverviewQueryContract() {

    private lateinit var fake: FakeAccountOverviewQuery

    @BeforeEach
    fun setUp() {
        fake = FakeAccountOverviewQuery()
    }

    override fun query(): AccountOverviewQuery = fake

    override fun persistAccount(accountId: String, balance: BigDecimal) {
        fake.seed(AccountOverviewView(accountId, balance, AccountTier.forBalance(balance)))
    }
}
