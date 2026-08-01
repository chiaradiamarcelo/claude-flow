package com.example.bank.api

import com.example.bank.api.dto.ApiError
import com.example.bank.domain.models.account.AccountNotFoundException
import com.example.bank.domain.models.account.InvalidDepositAmountException
import org.springframework.http.HttpStatus
import org.springframework.http.converter.HttpMessageNotReadableException
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.bind.annotation.ResponseStatus
import org.springframework.web.bind.annotation.RestControllerAdvice

@RestControllerAdvice
class ApiExceptionHandler {

    @ExceptionHandler(AccountNotFoundException::class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    fun handleAccountNotFound(exception: AccountNotFoundException): ApiError =
        ApiError(exception.message)

    @ExceptionHandler(InvalidDepositAmountException::class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    fun handleInvalidDepositAmount(exception: InvalidDepositAmountException): ApiError =
        ApiError(exception.message)

    @ExceptionHandler(HttpMessageNotReadableException::class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    fun handleMalformedRequestBody(exception: HttpMessageNotReadableException): ApiError =
        ApiError("Malformed request body")

    @ExceptionHandler(Exception::class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    fun handleUnexpectedFailure(exception: Exception): ApiError =
        ApiError("Unexpected error")
}
