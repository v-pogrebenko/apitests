import os
import json
import requests


class Test:
    def __init__(self, results_dir, sample_dir, tests_dir, errors_dir, encoding="utf-8"):
        """Class inintialization.

        :param results_dir: directory for restful responses.
        :param sample_dir: directory for samples.
        :param tests_dir: directory for restful requests.
        :param errors_dir: directory for error output file.
        :param encoding: file open encoding."""

        # since init is the only place where this function will be used.
        def force_dir(directory):
            """Ensures directory."""
            if not os.path.exists(directory):
                os.makedirs(directory)

        force_dir(results_dir)
        self._results = results_dir
        force_dir(sample_dir)
        self._sample = sample_dir
        self._tests = tests_dir
        force_dir(errors_dir)
        self._errors = errors_dir
        self._encoding = encoding

    def _get_request_content(self, name):
        """Reads request contents from a file.

        :param name: destination file name."""

        # complete file name.
        fn = os.path.join(self._tests, name + ".content")
        # GET requests usually don't have content part.
        if not os.path.exists(fn):
            return ""
        # return contents.
        with open(fn, encoding=self._encoding) as f:
            return f.read()

    def _send_request(self, ty, uri, headers, content, name):
        """Forms and sends request to given handler and write response to a file

        :param ty: request type.
        :param uri: request URI.
        :param headers: request headers.
        :param content: request content.
        :param name: destination file name."""

        # establishes connection, forms and prepeares a request then sends it.
        res = requests.Session().send(requests.Request(
            ty, uri, headers=headers, data=content).prepare())
        res_content = res.content.decode()
        # save result to a file.
        with open(os.path.join(self._results, name + ".result"), "w", encoding=self._encoding) as r:
            r.write(res_content)

        return res_content

    def _check_sample(self, name, res):
        """Compares response contents with a sample.

        :param name: destination file name.
        :param res: response contents."""

        # complete file name.
        fn = os.path.join(self._sample, name + ".sample")
        # compare result to sample.
        try:
            with open(fn, encoding=self._encoding) as s:
                # write an error if contents are not equal.
                if s.read() != res:
                    self._write_err(name)
        except FileNotFoundError:
            # if sample not exists (i.e. first run), make it.
            with open(fn, "w", encoding=self._encoding) as s:
                s.write(res)

    def _get_names(self):
        """Iterates through test files and get parameter names

        :rtype: list of filenames"""

        # list files in directory and sort them by name.
        files = os.listdir(self._tests)
        files.sort()
        # iterate through files and select parameter names.
        return [file.rstrip(".params") for file in files if ".params" in file]

    def _parse_param(self, fn):
        """Compares response contents with a sample.

        :param fn: destination file name.
        :rtype: tuple of request type, URI and headers"""

        # read request parameters.
        with open(os.path.join(self._tests, fn + ".params"), encoding=self._encoding) as f:
            j = json.loads(f.read())

        return j["Type"], j["URI"], j["Headers"]

    def run(self):
        """Run tests, get results, compare them to samples and check for errors."""

        # at the start of a new test remove old errors.
        self._remove_errors()
        # iterate through filenames, get corresponding data, do requests and compare results.
        for name in self._get_names():
            ty, uri, headers = self._parse_param(name)
            req_content = self._get_request_content(name)
            res_content = self._send_request(
                ty, uri, headers, req_content, name)
            self._check_sample(name, res_content)

    def _write_err(self, fn):
        """Writes given error to errors.txt

        :param fn: name of a file that contains an error."""

        # print to std out.
        msg = "ERROR during test # {} \n".format(fn)
        print(msg)
        # append to file.
        with open(os.path.join(self._errors, "errors.txt"), "a", encoding=self._encoding) as f:
            f.write(msg)

    def _remove_errors(self):
        """Removes errors.txt if exist."""

        try:
            os.remove(os.path.join(self._errors, "errors.txt"))
        except OSError:
            pass
