package com.example.bank.domain.models.account

import java.math.BigDecimal

class InvalidDepositAmountException(amount: BigDecimal) :
    RuntimeException("Deposit amount must be positive but was $amount")
