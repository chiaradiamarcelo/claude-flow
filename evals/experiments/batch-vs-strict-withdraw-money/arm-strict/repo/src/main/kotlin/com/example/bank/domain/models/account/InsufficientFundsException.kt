package com.example.bank.domain.models.account

import java.math.BigDecimal

class InsufficientFundsException(accountId: String, amount: BigDecimal) :
    RuntimeException("Account $accountId has insufficient funds to withdraw $amount")
