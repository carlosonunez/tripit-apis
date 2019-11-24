terraform {
  backend "s3" {}
}

// API Gateway requires that ACM certificates reside in us-east-1.
provider "aws" {
  alias = "aws_acm_cert_region_for_edge"
  region = "us-east-1"
}

variable "serverless_bucket_name" {
  description = "The bucket into which Serverless will deploy the app."
}

variable "app_account_name" {
  description = "The name to assign to the IAM user under which the API will run."
}

variable "domain_path" {
  description = "The DNS path to affix to the domain_tld."
}

variable "domain_tld" {
  description = "The domain name to use; this is used for creating HTTPS certificates."
}

variable "no_certs" {
  description = "Flag to disable cert provisioning for development deployments."
  default = "false"
}

variable "app_name" {
  description = "The name of the app for which APIs are being built."
}

data "aws_route53_zone" "app_dns_zone" {
  name = "${var.domain_tld}."
}

resource "aws_s3_bucket" "serverless_bucket" {
  bucket = "${var.serverless_bucket_name}"
}

resource "aws_iam_user" "app" {
  name = "${var.app_name}_api_app_account"
}

resource "aws_iam_access_key" "app" {
  user = "${aws_iam_user.app.name}"
}

resource "aws_iam_user_policy" "app" {
  name = "${var.app_name}_api_app_account_policy"
  user = "${aws_iam_user.app.name}"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
     {
        "Action": [
          "s3:ListObjects",
          "dynamodb:ListTables",
          "dynamodb:DescribeTable",
          "dynamodb:Query",
          "dynamodb:GetItem",
          "dynamodb:BatchGetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:BatchWriteItem"
        ],
        "Effect": "Allow",
        "Resource": "*"
     }
  ]
}
EOF
}

resource "aws_acm_certificate" "app_cert" {
  count = "${var.no_certs == "true" ? 0 : 1 }"
  provider = aws.aws_acm_cert_region_for_edge
  domain_name = "${var.domain_path}.${var.domain_tld}"
  validation_method = "DNS"
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "app_cert_validation_cname" {
  provider = aws.aws_acm_cert_region_for_edge
  count   = "${var.no_certs == "true" ? 0 : 1 }"
  name    = "${aws_acm_certificate.app_cert.0.domain_validation_options.0.resource_record_name}"
  type    = "${aws_acm_certificate.app_cert.0.domain_validation_options.0.resource_record_type}"
  zone_id = "${data.aws_route53_zone.app_dns_zone.id}"
  records = ["${aws_acm_certificate.app_cert.0.domain_validation_options.0.resource_record_value}"]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "app_cert" {
  provider = aws.aws_acm_cert_region_for_edge
  count = "${var.no_certs == "true" ? 0 : 1 }"
  certificate_arn         = "${aws_acm_certificate.app_cert.0.arn}"
  validation_record_fqdns = ["${aws_route53_record.app_cert_validation_cname.0.fqdn}"]
}

resource "aws_dynamodb_table" "state_associations" {
  name = "${var.app_name}_auth_state_tokens"
  hash_key = "access_key"
  read_capacity = 2
  write_capacity = 2
  attribute {
    name = "access_key"
    type = "S"
  }
}

resource "aws_dynamodb_table" "${var.app_name}_tokens" {
  name = "${var.app_name}_auth_state_state_associations"
  hash_key = "state_id"
  read_capacity = 2
  write_capacity = 2
  attribute {
    name = "state_id"
    type = "S"
  }
}

output "app_account_ak" {
  value = "${aws_iam_access_key.app.id}"
}

output "app_account_sk" {
  value = "${aws_iam_access_key.app.secret}"
}

output "certificate_arn" {
  value = "${var.no_certs == "true" ? "none" : aws_acm_certificate.app_cert.0.arn}"
}
