locals {
  dist_prefix = "../webapp/dist/"
}

resource "aws_s3_bucket_object" "dist" {
  for_each = fileset(path.module, "${local.dist_prefix}/**")

  bucket = aws_s3_bucket.b.bucket
  key    = substr(each.value, length(local.dist_prefix), length(each.value) - length(local.dist_prefix))
  source = "${path.module}/${each.value}"
  content_type = length(regexall("\\S\\.html", each.value)) > 0 ? "text/html" : length(regexall("\\S\\.js", each.value)) > 0 ? "text/javascript" : length(regexall("\\S\\.css", each.value)) > 0 ? "text/css" : null

  lifecycle {
    ignore_changes = [source]
  }
}
