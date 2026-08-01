package com.example.bank.api

class AccountNotFoundException(accountId: String) :
    RuntimeException("No account with id $accountId")
